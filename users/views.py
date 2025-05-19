from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, BasePermission
from .models import User
from .serializers import UserSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import ImageUploadSerializer


class GetMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.username == 'admin')

class GetAllUsersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class UserUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return self.request.user
    
    def perform_update(self, serializer):
        # Get the current avatar URL if it exists
        current_avatar = self.get_object().avatarUrl
        
        # If no new avatarUrl provided and no current one, set to default
        if 'avatarUrl' not in self.request.data and not current_avatar:
            serializer.save(avatarUrl="avatar1.jpeg")
        else:
            serializer.save()
    
    @swagger_auto_schema(
        operation_description="Get user profile information",
        responses={200: UserSerializer()}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update user profile information",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
                'avatarUrl': openapi.Schema(type=openapi.TYPE_STRING, description='URL for user avatar'),
            },
        ),
        responses={
            200: UserSerializer(),
            400: "Bad Request - Invalid data"
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Change user password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['current_password', 'new_password'],
            properties={
                'current_password': openapi.Schema(type=openapi.TYPE_STRING, description='Current password'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='New password'),
            },
        ),
        responses={
            200: openapi.Response(description="Password changed successfully"),
            400: "Bad Request - Invalid data or incorrect current password",
            401: "Unauthorized - User not authenticated"
        }
    )
    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response(
                {"error": "Both current password and new password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if current password is correct
        if not user.check_password(current_password):
            return Response(
                {"error": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set the new password
        user.set_password(new_password)
        user.save()
        
        return Response(
            {"message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )
    

class ImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        request_body=ImageUploadSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "qrCode": openapi.Schema(type=openapi.TYPE_STRING, description="URL of the uploaded QR code image"),
                },
            ),
            400: "Bad Request",
        },
    )
    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            image = serializer.validated_data["image"]
            try:
                # Upload the image to Cloudinary
                url = serializer.upload_to_cloudinary(image)
                
                # Update the user's qrCode field
                user = request.user
                user.qrCode = url
                user.save()

                return Response({"qrCode": url}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)