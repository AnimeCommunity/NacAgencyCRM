from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "is_active",
            "password",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {"password": {"write_only": True, "required": False}}

    def validate(self, attrs):
        request = self.context.get("request")
        if self.instance is not None and request and request.user == self.instance:
            requested_role = attrs.get("role", self.instance.role)
            requested_active = attrs.get("is_active", self.instance.is_active)
            if requested_role != "admin" or not requested_active:
                raise serializers.ValidationError(
                    "No puedes desactivar ni retirar el rol administrador de tu propia cuenta."
                )

        password = attrs.get("password")
        if self.instance is None and not password:
            raise serializers.ValidationError({"password": "Este campo es obligatorio."})
        if password:
            candidate = self.instance or User()
            for field in ("username", "first_name", "last_name", "email"):
                if field in attrs:
                    setattr(candidate, field, attrs[field])
            try:
                password_validation.validate_password(password, candidate)
            except Exception as exc:
                raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attribute, value in validated_data.items():
            setattr(instance, attribute, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        candidate = User(
            username=attrs.get("username", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
            email=attrs.get("email", ""),
            role="sales",
            is_active=False,
        )
        try:
            password_validation.validate_password(attrs["password"], candidate)
        except Exception as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(
            password=password,
            role="sales",
            is_active=False,
            **validated_data,
        )


class CRMTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        return token
