from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import RegistrationRequest
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from .permissions import IsScraperAllowed


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


User = get_user_model() 



@api_view(['POST'])
def register(request):
    email = request.data.get('email')

    if not email:
        return Response({'error': 'Email requis'}, status=400)

    # Vérifie si déjà utilisateur
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email déjà utilisé'}, status=400)

    # Vérifie si déjà une demande
    if RegistrationRequest.objects.filter(email=email).exists():
        return Response({'error': 'Demande déjà envoyée'}, status=400)

    # Créer demande
    RegistrationRequest.objects.create(email=email)

    return Response({'message': 'Demande envoyée, en attente de validation'})

#######################################################################

from django.contrib.auth import authenticate

@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, email=email, password=password)

    if user is not None:
        return Response({
            'message': 'Connexion réussie',
            'must_change_password': user.must_change_password
        })
    else:
        return Response({'error': 'Identifiants invalides'}, status=400)
    
############################################################################

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_profile(request):
    user = request.user

    password = request.data.get("password")
    username = request.data.get("username")

    if not password or not username:
        return Response({"error": "Champs requis"}, status=400)

    user.set_password(password)
    user.custom_username = username
    user.must_change_password = False

    user.save()

    return Response({"message": "Profil complété"})

#########################################################

# schedule/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Schedule
from .serializers import ScheduleSerializer
#Utilise le fichier permissions.py pour gérer les permissions d'accès aux vues de l'emploi du temps
from .permissions import IsAdminOrReadOnly

class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if getattr(user, "role", None) == "admin":
            return Schedule.objects.all()

        return Schedule.objects.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user

        if getattr(user, "role", None) == "admin":
            assigned_user_id = self.request.data.get("user")

            if assigned_user_id:
                try:
                    assigned_user = User.objects.get(id=assigned_user_id)
                except User.DoesNotExist:
                    assigned_user = user

                serializer.save(user=assigned_user)
            else:
                serializer.save(user=user)
        else:
            serializer.save(user=user)

##############################################################################################################
from .models import Course, Room
from .serializers import CourseSerializer, RoomSerializer
from rest_framework import viewsets



class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

################################################################################################################

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    
###########################################################################################################

# jobs/views.py
from rest_framework import viewsets
from .models import Job
from .serializers import JobSerializer
from rest_framework import viewsets, status

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all().order_by('id')
    serializer_class = JobSerializer
    permission_classes = [IsAdminOrReadOnly]



class JobScraperViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsScraperAllowed]

    def create(self, request, *args, **kwargs):
        data = request.data
        job_link = data.get("link")

        if not job_link:
            return Response({"error": "Le champ 'link' est requis."}, status=status.HTTP_400_BAD_REQUEST)

        # On prépare les données à insérer en enlevant le lien pour éviter les doublons d'arguments
        defaults = data.copy()
        # On s'assure que le lien n'est pas dans les defaults car il est déjà dans la recherche
        # Mais get_or_create gère souvent cela. Par sécurité, on fait ceci :
        
        job, created = Job.objects.get_or_create(
            link=job_link,
            defaults=defaults
        )

        if not created:
            # Code 200 : Le serveur dit "Ok, j'ai bien reçu, mais je n'ai rien créé de nouveau"
            return Response({"message": "Job already exists in database"}, status=status.HTTP_200_OK)

        # Code 201 : Nouveau job ajouté
        serializer = self.get_serializer(job)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    




############################################################################################################
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied




from rest_framework import serializers
from .models import HelpRequest, HelpResponse


class HelpResponseSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_id = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model = HelpResponse
        fields = ['id', 'user_name', 'user_id', 'content', 'is_accepted', 'created_at']

    def get_user_name(self, obj):
        return obj.user.custom_username or obj.user.email


class HelpRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_id = serializers.ReadOnlyField(source='user.id')
    responses = HelpResponseSerializer(many=True, read_only=True)

    class Meta:
        model = HelpRequest
        fields = [
            'id', 'user_name', 'user_id', 'title', 'description',
            'category', 'status', 'created_at', 'responses'
        ]

    def get_user_name(self, obj):
        return obj.user.custom_username or obj.user.email


# ✅ CLASSE MANQUANTE — ajoutée ici
class HelpRequestViewSet(viewsets.ModelViewSet):
    queryset = HelpRequest.objects.all().order_by('-created_at')
    serializer_class = HelpRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        help_request = self.get_object()
        serializer = HelpResponseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, help_request=help_request)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        help_request = self.get_object()
        if help_request.user != request.user:
            return Response({"error": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        help_request.status = 'resolved'
        help_request.save()
        return Response({"message": "Demande résolue"})


class HelpResponseViewSet(viewsets.ModelViewSet):
    queryset = HelpResponse.objects.all()
    serializer_class = HelpResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        response = self.get_object()
        if response.help_request.user != request.user:
            raise PermissionDenied("Vous ne pouvez pas accepter cette réponse.")
        HelpResponse.objects.filter(help_request=response.help_request).update(is_accepted=False)
        response.is_accepted = True
        response.save()
        return Response({"message": "Réponse acceptée"})
    

from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users(request):
    users = User.objects.all()

    data = [
        {
            "id": u.id,
            "email": u.email,
            "custom_username": u.custom_username,
            "role": getattr(u, "role", None)
        }
        for u in users
    ]

    return Response(data)