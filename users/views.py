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

        if not user.is_authenticated:
            return Schedule.objects.none()

        if getattr(user, "role", None) == "admin":
            return Schedule.objects.all()

        return Schedule.objects.filter(user=user)
    
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