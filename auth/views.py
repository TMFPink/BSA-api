from django.contrib.auth import authenticate
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from users.serializers import UserSerializer, LoginSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.authentication import JWTAuthentication  # Add this import

def get_first_error_message(detail):
    """
    Return only the first error message from DRF error detail.
    For example, if detail is:
    {
      "username": ["User with this username already exists."],
      "email": ["Enter a valid email address."]
    }
    This function returns "User with this username already exists."
    """
    # If it's a dictionary of field -> list of messages
    if isinstance(detail, dict):
        for field, messages in detail.items():
            # If messages is a list, return the first item
            if isinstance(messages, list) and len(messages) > 0:
                return str(messages[0])
            # Otherwise, just return the string representation
            return str(messages)

    # If it's already a list, return the first element
    if isinstance(detail, list) and len(detail) > 0:
        return str(detail[0])

    # Otherwise, just convert it to a string
    return str(detail)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            return Response({
                "message": "User registered successfully",
                "data": response.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            error_message = str(e)
            if hasattr(e, 'detail'):
                error_message = get_first_error_message(e.detail)

            return Response({
                "error": error_message
            }, status=status.HTTP_400_BAD_REQUEST)
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "refreshToken": "string",
                        "accessToken": "string"
                    }
                }
            ),
            401: "Invalid Credentials",
            404: "User not found"
        }
    )
    def post(self, request):
        try:
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
                'refreshToken': str(refresh),
                'accessToken': str(refresh.access_token)
            })
        except Exception as e:
            error_message = str(e)
            if hasattr(e, 'detail'):
                error_message = e.detail
            return Response({
                "error": error_message
            }, status=status.HTTP_400_BAD_REQUEST)
