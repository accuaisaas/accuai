from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from accuai_backend.users.api.views import UserViewSet

# from accounts.api.views import LoginApiViewSet
from product.api.views import ProductViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("product", ProductViewSet, basename="product")
# Add the login view to the router
# router.register(r"accounts/login", LoginApiViewSet, basename="login")


app_name = "api"
urlpatterns = router.urls
