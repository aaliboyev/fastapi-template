import abc


class BaseService(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs): ...


class BaseServiceProvider(abc.ABC):
    _service: BaseService
    _service_class: type[BaseService]
    _service_name: str
    _services: dict[str, type[BaseService]]

    def __init__(self, service: str, *args, skip_service_init=False, **kwargs):
        if service not in self._services:
            raise ValueError(f"Service '{service}' not registered.")

        self._service_class = self._services[service]
        self._service_name = service

        if not skip_service_init:
            self._initialize_service(*args, **kwargs)

    def _initialize_service(self, *args, **kwargs):
        self._service = self._service_class(*args, **kwargs)
