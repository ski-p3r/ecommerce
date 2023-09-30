from django.template.loader import render_to_string
from django.urls import reverse
from rest_framework import status, views
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
import jwt
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User
from .serializers import RegisterSerializer, EmailVerificationSerializer

class RegisterView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        user = User.objects.get(email=user_data['email'])
        email = user.email
        name = f"{user.first_name} {user.last_name}"
        current_site = get_current_site(request)
        email_verification_url = reverse('activate')  # Adjust this to match your URL pattern
        token = RefreshToken.for_user(user).access_token
        absurl = f'http://{current_site}{email_verification_url}?token={str(token)}'

        # Modify your HTML message with dynamic data
        message = render_to_string('activation.html', {
            'full_name': name,
            'urls': absurl,
        })

        # Your inline CSS styles
        inline_styles = """
        <style>
        /* Add your CSS styles here */
        body {
            background-color: #e9ecef;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #ffffff;
        }
        h1 {
            font-size: 32px;
            font-weight: 700;
            color: #666666;
            
        }
        p {
            font-size: 16px;
            line-height: 24px;
            color: #666666;
        }
        a.button {
            display: inline-block;
            background-color: #007bff;
            color: #ffffff;
            padding: 10px 20px;
            text-decoration: none;
        }
        </style>
        """

        # Add the inline CSS styles to the HTML message
        message = f"{inline_styles}{message}"

        email_subject = 'Verify your email'
        to_email = email

        try:
            send_email = EmailMessage(email_subject, message, to=[to_email])
            send_email.content_subtype = 'html'  # Set the content type to HTML
            send_email.send()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Handle email sending errors
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from django.conf import settings

# ... (other imports)

class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    token_param_config = openapi.Parameter(
        'token', in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get('token')
        try:
            print("Received token:", token)  # Debugging: Print the received token
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            print("Decoded token:", decoded_token)  # Debugging: Print the decoded token
            user_id = decoded_token.get('user_id')
            
            if user_id is not None:
                user = User.objects.get(id=user_id)
                if not user.is_active:
                    user.is_active = True
                    user.save()
                    return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'User is already verified'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Invalid user_id in token'}, status=status.HTTP_400_BAD_REQUEST)
            
        except jwt.ExpiredSignatureError as e:
            print("Expired Signature Error:", e)  # Debugging: Print the exception
            return Response({'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError as e:
            print("Decode Error:", e)  # Debugging: Print the exception
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist as e:
            print("User Does Not Exist Error:", e)  # Debugging: Print the exception
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
