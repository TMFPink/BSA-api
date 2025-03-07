from django.contrib.auth import authenticate
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from users.serializers import UserSerializer, LoginSerializer
from drf_yasg.utils import swagger_auto_schema  # Add this import
from drf_yasg import openapi  # Add this import

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "User registered successfully",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "refresh-token": "string",
                        "access-token": "string"
                    }
                }
            ),
            401: "Invalid Credentials",
            404: "User not found"
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = User.objects.filter(username=username).first()
        if user is None:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not user.check_password(password):
            return Response({"error": "Wrong password"}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh-token': str(refresh),
            'access-token': str(refresh.access_token),
        })
