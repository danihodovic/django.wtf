from factory import Faker, SubFactory, lazy_attribute
from factory.django import DjangoModelFactory

from .models import Profile, Repository, RepositoryStars, RepositoryType, UserType


class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = Profile

    github_id = Faker("pyint")
    login = Faker("slug")
    type = Faker("random_element", elements=UserType.values)
    avatar_url = Faker("image_url")


class RepositoryFactory(DjangoModelFactory):
    class Meta:
        model = Repository

    @lazy_attribute
    def full_name(self):
        return self.owner.login + "/" + self.name

    github_id = Faker("pyint")
    owner = SubFactory(ProfileFactory)
    name = Faker("slug")
    forks = Faker("pyint")
    open_issues = Faker("pyint")
    watchers = Faker("pyint")
    stars = Faker("pyint")
    archived = Faker("pybool")
    description = Faker("sentence")
    topics = Faker("paragraphs")
    type = Faker("random_element", elements=RepositoryType.values)


class RepositoryStarsFactory(DjangoModelFactory):
    class Meta:
        model = RepositoryStars

    repository = SubFactory(RepositoryFactory)
    stars = Faker("pyint")
    created_at = Faker("date")
