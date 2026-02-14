from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Vault, VaultMembership, RoleChoices


@receiver(post_save, sender=Vault)
def create_owner_membership(sender, instance, created, **kwargs):
    """
    Automatically create OWNER membership for vault creator when vault is created.
    """
    if created:
        VaultMembership.objects.create(
            vault=instance,
            user=instance.owner,
            role=RoleChoices.OWNER,
            added_by=instance.owner
        )
