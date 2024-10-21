from django.contrib import admin

from .models import Dishes
from .models import Trash
from .models import Bathroom_one
from .models import Bathroom_two
from .models import Playroom
from .models import Vacuum
from .models import Dust
from .models import DateTimeField

admin.site.register(Dishes)
admin.site.register(Trash)
admin.site.register(Bathroom_one)
admin.site.register(Bathroom_two)
admin.site.register(Playroom)
admin.site.register(Vacuum)
admin.site.register(Dust)
admin.site.register(DateTimeField)