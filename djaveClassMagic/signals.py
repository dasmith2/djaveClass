"""
The ability to utterly destroy all data for a particular user is important for
2 reasons.

First, it's a handy way to clean up after a web demo.

Second, user's ought to be able to request that all their data be utterly
destroyed from the system. Entire careers at Google are built on this
surprisingly difficult requirement, which is why it's a good idea to get out
ahead of it.

Anything with a foreign key to user should do, like,

@receiver(destroy_user, sender=User)
def destroy_user_foos(sender, destroy_object):
  for foo in Foo.objects.filter(user=destroy_object):
    destroy_user.send(sender=Foo, destroy_object=foo)
    foo.delete()

class Foo(models.Model):
  user = models.ForeignKey(User, on_delete=models.PROTECT)

Anything 1 or more foreign keys removed from User should do, like,

@receiver(destroy_user, sender=Foo)
def destroy_user_bars(sender, destroy_object):
  for bar in destroy_object.bar_set.all():
    bar.delete()

class Bar(models.Model):
  foo = models.ForeignKey(Foo, on_delete=models.PROTECT)
"""
from django.contrib.auth.models import User
import django.dispatch


destroy_user = django.dispatch.Signal(providing_args=['destroy_object'])


def do_destroy_user(user):
  destroy_user.send(sender=User, destroy_object=user)
  user.delete()
