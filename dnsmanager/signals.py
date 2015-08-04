import django.dispatch

# signal
zone_fully_saved_signal = django.dispatch.Signal(providing_args=["instance", "created"])