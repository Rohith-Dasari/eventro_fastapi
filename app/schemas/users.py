from pydantic import BaseModel, ConfigDict, EmailStr, Field
from models.users import User


class UserProfile(BaseModel):
	model_config = ConfigDict(populate_by_name=True, from_attributes=True)

	user_id: str = Field(serialization_alias="UserID")
	username: str = Field(serialization_alias="Username")
	email: EmailStr = Field(serialization_alias="Email")
	phone_number: str = Field(serialization_alias="PhoneNumber")
	role: str = Field(serialization_alias="Role")
	is_blocked: bool = Field(serialization_alias="IsBlocked")

	@classmethod
	def from_domain(cls, user: User) -> "UserProfile":
		return cls(
			user_id=user.user_id,
			username=user.username,
			email=user.email,
			phone_number=user.phone_number,
			role=user.role.value.title(),
			is_blocked=user.is_blocked,
		)
