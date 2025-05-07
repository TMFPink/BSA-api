from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Bill, BillParticipant, BillDetail
from .serializers import BillParticipantSerializer, BillSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from friends.models import Friends
from users.models import User
from rest_framework import status
from utils.hash import decode_hashed_id, hash_id
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser, FormParser
from utils.extract_image import extract_bill_data
from .serializers import BillImageUploadSerializer, BillFromImageResponseSerializer

class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer

class BillListCreateView(generics.ListCreateAPIView):
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Bill.objects.filter(
            id__in=BillParticipant.objects.filter(user=self.request.user).values_list('bill_id', flat=True)
        ).order_by('-created_at')  # Order by created_at in descending order (new to old)

        # Get filter parameters from request
        billName = self.request.query_params.get("billName", None)
        category = self.request.query_params.get("category", None)
        all_paid = self.request.query_params.get("all_paid", None)  # Payment Status
        date = self.request.query_params.get("date", None)  # Bill Date
        
        # Apply filters if they are provided
        if billName:
            queryset = queryset.filter(billName__icontains=billName)
        
        if category:
            queryset = queryset.filter(category__icontains=category)
        
        if all_paid is not None:
            # Convert string to boolean
            is_paid = all_paid.lower() == 'true'
            queryset = queryset.filter(all_paid=is_paid)
        
        if date:            
            queryset = queryset.filter(created_at__date=date)
            
        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('billName', openapi.IN_QUERY, description="Filter by bill name", type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category", type=openapi.TYPE_STRING),
            openapi.Parameter('all_paid', openapi.IN_QUERY, description="Filter by payment status (true/false)", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('date', openapi.IN_QUERY, description="Filter by bill date (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
        ],
        responses={200: BillSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def perform_create(self, serializer):
        participants_data = self.request.data.get('participants', [])
        payer_data = self.request.data.get('payer', None)

        # Validate participants
        valid_participants = []
        for participant in participants_data:
            user_id = decode_hashed_id(participant['id'], User)
            user = get_object_or_404(User, id=user_id)
            valid_participants.append(user)

        # Validate payer
        if payer_data == "":  # Handle empty string for payer
            payer_data = None
        if payer_data:
            payer_id = decode_hashed_id(payer_data, User)
            payer = get_object_or_404(User, id=payer_id)
            # Ensure payer is part of participants
            if payer not in valid_participants:
                raise ValidationError({"payer": "Payer must be one of the participants."})
        else:
            payer = None

        # Save the serializer with validated data
        serializer.save(payer=payer)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'billName': openapi.Schema(type=openapi.TYPE_STRING, description='billName of the bill'),
                'category': openapi.Schema(type=openapi.TYPE_STRING, description='Category of the bill'),
                'date': openapi.Schema(type=openapi.FORMAT_DATETIME, description='Creation date of the bill'),
                'shared': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether the bill is shared'),
                'billDetails': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the item'),
                            'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Price of the item'),
                            'user': openapi.Schema(type=openapi.TYPE_STRING, description='Hashed user ID', nullable=True),  # Made optional
                        }
                    ),
                    description='List of bill details'
                ),
                'participants': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_STRING, description='Hashed participant ID'),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the participant'),
                            'split_amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Split amount for the participant'),
                            'paid': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether the participant has paid'),
                        }
                    ),
                    description='List of participants'
                ),
                'payer': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, description='Hashed payer ID'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the payer'),
                        'split_amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Split amount for the payer'),
                        'paid': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether the payer has paid'),
                    },
                    description='Payer details'
                ),
                'allPaid': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether all participants have paid'),
            },
            required=['billName', 'category', 'date', 'shared', 'billDetails', 'participants']  # Remove 'user' from required fields
        ),
        responses={201: BillSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class BillDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BillSerializer

    def get_object(self):
        # Get the hashed bill ID from the URL
        hashed_id = self.kwargs.get("hashed_id")

        # Decode it to get the original bill ID
        bill_id = decode_hashed_id(hashed_id, Bill)

        if not bill_id:
            return get_object_or_404(Bill, id=-1)  # Return 404 if invalid ID

        # Ensure the user has access to the bill
        return get_object_or_404(
            Bill, 
            id=bill_id, 
            id__in=BillParticipant.objects.filter(user=self.request.user).values_list("bill_id", flat=True)
        )

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('hashed_id', openapi.IN_PATH, description="Hashed bill ID", type=openapi.TYPE_STRING)
        ],
        responses={200: BillSerializer}
    )
    def get(self, request, *args, **kwargs):
        bill = self.get_object()
        serializer = self.get_serializer(bill)
        data = serializer.data

        # Modify the payer field to include only the username
        if bill.payer:
            data['payer'] = bill.payer.username
        else:
            data['payer'] = None

        return Response(data)

class BillUpdateView(generics.UpdateAPIView):
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Get the hashed bill ID from the URL
        hashed_id = self.kwargs.get("hashed_id")

        # Decode it to get the original bill ID
        bill_id = decode_hashed_id(hashed_id, Bill)

        if not bill_id:
            return get_object_or_404(Bill, id=-1)  # Return 404 if invalid ID

        # Ensure the user has access to the bill
        return get_object_or_404(
            Bill, 
            id=bill_id, 
            id__in=BillParticipant.objects.filter(user=self.request.user).values_list("bill_id", flat=True)
        )

    def perform_update(self, serializer):
        bill = serializer.save()
        participants_data = self.request.data.get("participants", [])

        if participants_data:
            if not isinstance(participants_data, list):
                raise ValidationError({"participants": "Participants must be a list of hashed user IDs."})

            valid_friends = [decode_hashed_id(fid, User) for fid in participants_data]
            valid_friends = [friend for friend in valid_friends if friend]

            if not valid_friends:
                raise ValidationError({"participants": "Invalid participant IDs."})

            total_participants = len(valid_friends) + 1  # Including the creator
            split_amount = bill.total_amount / total_participants

            BillParticipant.objects.filter(bill=bill).delete()
            BillParticipant.objects.create(bill=bill, user=self.request.user, is_paid=True, split_amount=split_amount)

            for friend_id in valid_friends:
                friend = get_object_or_404(User, id=friend_id)
                if not Friends.objects.filter(user=self.request.user, friend=friend).exists():
                    raise ValidationError({"participants": f"{friend.username} is not your friend!"})
                BillParticipant.objects.create(bill=bill, user=friend, split_amount=split_amount)

        return bill

class PayBillView(generics.UpdateAPIView):
    serializer_class = BillParticipantSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(is_paid=True)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="Primary key of the bill participant", type=openapi.TYPE_INTEGER)
        ],
        request_body=BillParticipantSerializer,
        responses={200: BillParticipantSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

class AddParticipantsToBillView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'bill_id': openapi.Schema(type=openapi.TYPE_STRING, description='Hashed bill ID'),
                'participants': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description='List of hashed participant IDs'
                ),
            },
            required=['bill_id', 'participants']
        ),
        responses={201: "Participants added successfully!"}
    )
    def post(self, request):

        encoded_bill_id = request.data.get("bill_id")
        bill_id = decode_hashed_id(encoded_bill_id, Bill)
        if not bill_id:
            return Response({"error": "Invalid bill ID."}, status=status.HTTP_400_BAD_REQUEST)
        bill = get_object_or_404(Bill, id=bill_id)


        hashed_friend_ids = request.data.get("participants", [])
        if not isinstance(hashed_friend_ids, list) or not hashed_friend_ids:
            return Response({"error": "Participants must be a list of hashed user IDs."}, status=status.HTTP_400_BAD_REQUEST)

        # Decode the hashed user IDs
        valid_friends = [decode_hashed_id(fid, User) for fid in hashed_friend_ids]
        valid_friends = [friend for friend in valid_friends if friend]  # Remove None values

        if not valid_friends:
            return Response({"error": "Invalid participant IDs."}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure all provided users are friends of the requester
        for friend in valid_friends:
            friend = get_object_or_404(User, id=friend)
            if not Friends.objects.filter(user=request.user, friend=friend).exists():
                return Response(
                    {"error": f"{friend.username} is not your friend!"},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Calculate how much each participant should owe (including new participants)
        total_participants = bill.participants.count() + len(valid_friends)
        split_amount = bill.total_amount / total_participants

        # Update existing participants' owed amount
        for participant in bill.participants.all():
            participant.split_amount = split_amount
            participant.save()

        # Add new participants
        new_participants = []
        for friend in valid_friends:
            friend = get_object_or_404(User, id=friend)
            participant, created = BillParticipant.objects.get_or_create(
                bill=bill, user=friend, defaults={"split_amount": split_amount}
            )
            if not created:
                participant.split_amount = split_amount
                participant.save()
            new_participants.append(participant)

        # Hash the participant IDs before returning the response
        hashed_participants = [
            {
                "id": hash_id(participant.id),
                "user": {
                    "id": hash_id(participant.user.id),
                    "username": participant.user.username
                },
                "split_amount": participant.split_amount,  # Include split_amount
                "is_paid": participant.is_paid,
            }
            for participant in new_participants
        ]

        return Response(hashed_participants, status=status.HTTP_201_CREATED)
    



# Add this new view class to your views.py file
class ProcessBillImageView(APIView): 
    # permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['post']  
    
    @swagger_auto_schema(
        request_body=BillImageUploadSerializer,
        responses={
            200: BillFromImageResponseSerializer,
            400: "Bad Request",
            401: "Unauthorized"
        },
        operation_description="Upload a bill image to extract information without saving the image"
    )
    
    def post(self, request):
        serializer = BillImageUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            image_file = serializer.validated_data['image']
            
            # Extract bill data using OpenAI
            result = extract_bill_data(image_file)
            
            # Return the extracted data
            return Response(result, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)