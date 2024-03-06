from django.db import models


class PypiRelease(models.Model):
    project = models.ForeignKey(
        "core.PypiProject",
        on_delete=models.CASCADE,
    )
    version = models.CharField(max_length=30)
    uploaded_at = models.DateTimeField()

    class Meta:
        unique_together = [["project", "version"]]

    def __str__(self):
        version = self.version
        return f"<PypiRelease: {self.project.repository.full_name} {version=}>"

    def pypi_release_url(self):
        return (
            f"https://pypi.org/project/{self.project.repository.name}/{self.version}/"
        )
