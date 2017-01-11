"""household URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

from edc_constants.constants import UUID_PATTERN

from plot.patterns import plot_identifier
from survey.patterns import survey

from .admin_site import household_admin
from .patterns import household_identifier
from .views import ListBoardView

urlpatterns = [
    url(r'^admin/', household_admin.urls),
    url(r'^listboard/(?P<page>\d+)/', ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/(?P<plot_identifier>' + plot_identifier + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/(?P<household_identifier>' + household_identifier + ')/(?P<survey>' + survey + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/(?P<household_identifier>' + household_identifier + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/(?P<household_identifier>' + household_identifier + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/(?P<household_structure>' + UUID_PATTERN.pattern + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/(?P<household>' + UUID_PATTERN.pattern + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/', ListBoardView.as_view(), name='listboard_url'),
]
