import re

from rest_framework import serializers

from .models import ContactMessage, NewsletterSubscriber


class FAQQuestionSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=3, max_length=2000)


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Enter your name.")
        return value

    def validate_phone(self, value):
        value = value.strip()
        if not re.fullmatch(r"\+?[0-9\s()-]{7,20}", value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate_subject(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Enter a subject.")
        return value

    def validate_message(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Enter a message.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            validated_data["user"] = user
        return super().create(validated_data)


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[])

    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]

    def validate_email(self, value):
        return value.strip().casefold()

    def create(self, validated_data):
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=validated_data["email"],
        )
        if not created and not subscriber.is_active:
            subscriber.is_active = True
            subscriber.unsubscribed_at = None
            subscriber.save(update_fields=["is_active", "unsubscribed_at"])
        return subscriber
