import pytest
import bcrypt

from app.services.user_service import UserService
from models.users import User, Role
from schemas.users import UserProfile
from custom_exceptions.generic import NotFoundException
from custom_exceptions.user_exceptions import IncorrectCredentials, UserAlreadyExists


class FakeUserRepo:
	def __init__(self):
		self.by_id = {}

	def get_by_id(self, user_id: str):
		return self.by_id.get(user_id)

	def get_by_mail(self, mail: str):
		for user in self.by_id.values():
			if user.email == mail:
				return user
		return None

	def add_user(self, user: User):
		self.by_id[user.user_id] = user


@pytest.fixture
def fake_repo():
	return FakeUserRepo()


@pytest.fixture
def service(fake_repo):
	return UserService(user_repo=fake_repo)


def test_get_user_by_id_happy_path(service, fake_repo):
	user = User(
		user_id="u1",
		username="alice",
		email="alice@example.com",
		phone_number="1234567890",
		password="hashed",
		role=Role.CUSTOMER,
		is_blocked=False,
	)
	fake_repo.add_user(user)

	result = service.get_user_by_id("u1")

	assert result is user


def test_get_user_by_id_not_found(service):
	with pytest.raises(NotFoundException):
		service.get_user_by_id("missing")


def test_get_user_profile_maps_fields(service, fake_repo):
	user = User(
		user_id="u1",
		username="alice",
		email="alice@example.com",
		phone_number="1234567890",
		password="hashed",
		role=Role.CUSTOMER,
		is_blocked=False,
	)
	fake_repo.add_user(user)

	profile = service.get_user_profile("u1")

	assert isinstance(profile, UserProfile)
	assert profile.user_id == "u1"
	assert profile.username == "alice"
	assert profile.email == "alice@example.com"
	assert profile.phone_number == "1234567890"
	assert profile.role == "Customer"
	assert profile.is_blocked is False


def test_get_user_by_mail_not_found(service):
	with pytest.raises(NotFoundException):
		service.get_user_by_mail("none@example.com")


def test_login_success(service, fake_repo, monkeypatch):
	password = "ValidPass!1234"
	hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
	user = User(
		user_id="u1",
		username="alice",
		email="alice@example.com",
		phone_number="1234567890",
		password=hashed,
		role=Role.CUSTOMER,
		is_blocked=False,
	)
	fake_repo.add_user(user)

	monkeypatch.setattr("app.services.user_service.create_jwt", lambda *_: "token")

	token = service.login(email="alice@example.com", password=password)

	assert token == "token"


def test_login_bad_password(service, fake_repo):
	hashed = bcrypt.hashpw("Correct!1234".encode(), bcrypt.gensalt()).decode()
	user = User(
		user_id="u1",
		username="alice",
		email="alice@example.com",
		phone_number="1234567890",
		password=hashed,
		role=Role.CUSTOMER,
		is_blocked=False,
	)
	fake_repo.add_user(user)

	with pytest.raises(IncorrectCredentials):
		service.login(email="alice@example.com", password="WrongPassword!123")


def test_signup_success_creates_and_returns_token(service, fake_repo, monkeypatch):
	monkeypatch.setattr("app.services.user_service.create_jwt", lambda *_: "token")

	token = service.signup(
		email="new@example.com",
		username="newuser",
		password="GoodPass!1234",
		phone="1234567890",
	)

	assert token == "token"
	assert len(fake_repo.by_id) == 1
	saved_user = next(iter(fake_repo.by_id.values()))
	assert saved_user.email == "new@example.com"
	assert saved_user.username == "newuser"
	assert saved_user.phone_number == "1234567890"
	assert saved_user.role == Role.CUSTOMER


def test_signup_duplicate_email_raises(service, fake_repo):
	fake_repo.add_user(
		User(
			user_id="u1",
			username="existing",
			email="dupe@example.com",
			phone_number="1234567890",
			password="hashed",
			role=Role.CUSTOMER,
			is_blocked=False,
		)
	)

	with pytest.raises(UserAlreadyExists):
		service.signup(
			email="dupe@example.com",
			username="newuser",
			password="GoodPass!1234",
			phone="1234567890",
		)


def test_signup_invalid_email_raises(service):
	with pytest.raises(ValueError):
		service.signup(
			email="invalid-email",
			username="user",
			password="GoodPass!1234",
			phone="1234567890",
		)


def test_signup_invalid_password_raises(service):
	with pytest.raises(ValueError):
		service.signup(
			email="ok@example.com",
			username="user",
			password="short",
			phone="1234567890",
		)


def test_signup_invalid_phone_raises(service):
	with pytest.raises(ValueError):
		service.signup(
			email="ok@example.com",
			username="user",
			password="GoodPass!1234",
			phone="123",
		)
