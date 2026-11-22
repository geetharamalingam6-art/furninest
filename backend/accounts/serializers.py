from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Address, UserProfile

User = get_user_model()


class UserSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "phone_number", "is_staff", "email_verified", "date_joined"]

    def get_full_name(self, user):
        return user.get_full_name().strip()


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value):
        value = value.strip().casefold()
        if User.objects.filter(Q(email__iexact=value) | Q(pending_email__iexact=value)).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        name_parts = attrs["full_name"].strip().split(maxsplit=1)
        if not name_parts or not name_parts[0]:
            raise serializers.ValidationError({"full_name": "Enter your name."})
        attrs["first_name"] = name_parts[0]
        attrs["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
        try:
            password_validation.validate_password(attrs["password"])
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": list(error.messages)}) from error
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        validated_data.pop("full_name")
        user = User.objects.create_user(password=password, **validated_data)
        UserProfile.objects.create(user=user)
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        attrs[self.username_field] = attrs[self.username_field].strip().casefold()
        user = User.objects.filter(email__iexact=attrs[self.username_field]).first()
        if user and user.check_password(attrs.get("password", "")) and not user.email_verified:
            raise serializers.ValidationError(
                {"detail": "Please verify your email address before signing in."}
            )
        data = super().validate(attrs)
        data["user"] = UserSummarySerializer(self.user).data
        return data


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", max_length=20, required=False, allow_blank=True)
    full_name = serializers.CharField(max_length=150, required=False)

    class Meta:
        model = UserProfile
        fields = ["email", "full_name", "phone_number", "avatar"]

    def to_representation(self, instance):
        return {
            "email": instance.user.email,
            "email_verified": instance.user.email_verified,
            "date_joined": instance.user.date_joined,
            "full_name": instance.user.get_full_name().strip(),
            "phone_number": instance.user.phone_number,
            "avatar": self.fields["avatar"].to_representation(instance.avatar),
        }

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        full_name = validated_data.pop("full_name", None)
        if full_name is not None:
            name_parts = full_name.strip().split(maxsplit=1)
            if not name_parts or not name_parts[0]:
                raise serializers.ValidationError({"full_name": "Enter your name."})
            user_data["first_name"] = name_parts[0]
            user_data["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
        for field, value in user_data.items():
            setattr(instance.user, field, value)
        if user_data:
            instance.user.save(update_fields=list(user_data.keys()))
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if validated_data:
            instance.save(update_fields=[*validated_data.keys(), "updated_at"])
        return instance


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        exclude = ["user", "created_at", "updated_at"]
        read_only_fields = ["id"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"old_password": "The current password is incorrect."})
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        try:
            password_validation.validate_password(attrs["new_password"], user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"new_password": list(error.messages)}) from error
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerificationResendSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=False,
    )


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User._default_manager.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as error:
            raise serializers.ValidationError({"uid": "This password reset link is invalid."}) from error

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "This password reset link is invalid or expired."})
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        try:
            password_validation.validate_password(attrs["new_password"], user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"new_password": list(error.messages)}) from error
        attrs["user"] = user
        return attrs
