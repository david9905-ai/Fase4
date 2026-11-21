"""Sistema en memoria para gestionar clientes, servicios y reservas.

Ejecuta este archivo con: python sistema_gestion.py
Los errores se registran en sistema_gestion.log.
"""

from abc import ABC, abstractmethod
from enum import Enum
import logging
import math
import re
from typing import Dict, List, Optional, Union

def configurar_logs() -> logging.Logger:
    """Configura el registro en archivo y usa consola si el archivo no se puede abrir."""
    logger = logging.getLogger("sistema_gestion")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    try:
        archivo = logging.FileHandler("sistema_gestion.log", encoding="utf-8")
        archivo.setFormatter(formato)
        logger.addHandler(archivo)
    except OSError as exc:
        consola = logging.StreamHandler()
        consola.setFormatter(formato)
        logger.addHandler(consola)
        logger.exception(
            "No se pudo abrir el archivo de logs; se usará la consola."
        )
    return logger


LOG = configurar_logs()


# Excepciones personalizadas
class SistemaGestionError(Exception):
    """Excepción base del sistema."""


class ValidacionError(SistemaGestionError):
    """Un dato de entrada no cumple las reglas de validación."""


class EntidadDuplicadaError(SistemaGestionError):
    """Se intentó registrar una entidad que ya existe."""


class EntidadNoEncontradaError(SistemaGestionError):
    """No se encontró la entidad solicitada."""


class EstadoReservaError(SistemaGestionError):
    """La reserva no permite la operación solicitada en su estado actual."""


class ReservaError(SistemaGestionError):
    """Error al crear o procesar una reserva."""


class EntidadSistema(ABC):
    """Contrato común para las entidades del sistema."""

    def __init__(self, nombre: str) -> None:
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValidacionError("El nombre no puede estar vacío.")
        self._nombre = nombre.strip()

    @property
    def nombre(self) -> str:
        return self._nombre

    @abstractmethod
    def definir_entidad(self) -> str:
        """Devuelve una descripción breve del tipo de entidad."""
        raise NotImplementedError


class Cliente(EntidadSistema):
    """Cliente con datos personales validados y atributos encapsulados."""

    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(
        self,
        nombre: str,
        cedula: str,
        telefono: str,
        correo_electronico: str,
    ) -> None:
        super().__init__(nombre)
        try:
            self._cedula = self._validar_cedula(cedula)
            self._telefono = self._validar_telefono(telefono)
            self._correo_electronico = self._validar_correo(correo_electronico)
        except (TypeError, ValueError) as exc:
            LOG.exception("No se pudieron validar los datos de un cliente.")
            raise ValidacionError("Los datos del cliente no son válidos.") from exc

    @staticmethod
    def _validar_cedula(cedula: str) -> str:
        if not isinstance(cedula, str):
            raise TypeError("La cédula debe ser texto.")
        limpia = re.sub(r"[\s.-]", "", cedula)
        if not limpia.isdigit() or not 5 <= len(limpia) <= 15:
            raise ValueError("La cédula debe contener entre 5 y 15 dígitos.")
        return limpia

    @staticmethod
    def _validar_telefono(telefono: str) -> str:
        if not isinstance(telefono, str):
            raise TypeError("El teléfono debe ser texto.")
        limpia = re.sub(r"[\s()+.-]", "", telefono)
        if not limpia.isdigit() or not 7 <= len(limpia) <= 15:
            raise ValueError("El teléfono debe contener entre 7 y 15 dígitos.")
        return limpia

    @classmethod
    def _validar_correo(cls, correo: str) -> str:
        if not isinstance(correo, str) or not cls.EMAIL_RE.fullmatch(correo.strip()):
            raise ValueError("El correo electrónico no tiene un formato válido.")
        return correo.strip().lower()

    @property
    def cedula(self) -> str:
        return self._cedula

    @property
    def telefono(self) -> str:
        return self._telefono

    @property
    def correo_electronico(self) -> str:
        return self._correo_electronico

    def validar_datos(self) -> bool:
        """Los datos ya se validaron al construir el objeto."""
        return True

    def definir_entidad(self) -> str:
        return "Cliente"

    def __repr__(self) -> str:
        return "Cliente(nombre={!r})".format(self.nombre)


class Servicio(EntidadSistema, ABC):
    """Clase abstracta para servicios con cálculo y validación polimórficos."""

    def __init__(self, nombre: str, tarifa: float) -> None:
        super().__init__(nombre)
        try:
            tarifa = float(tarifa)
        except (TypeError, ValueError) as exc:
            LOG.exception("La tarifa del servicio no es numérica.")
            raise ValidacionError("La tarifa debe ser un número.") from exc
        if not math.isfinite(tarifa) or tarifa <= 0:
            raise ValidacionError(
                "La tarifa debe ser un número finito mayor que cero."
            )
        self._tarifa = tarifa

    @property
    def tarifa(self) -> float:
        return self._tarifa

    @abstractmethod
    def calcular_precio(self, duracion: float) -> float:
        """Calcula el costo según la duración del servicio."""
        raise NotImplementedError

    @abstractmethod
    def describir_servicio(self) -> str:
        """Describe el servicio para el usuario."""
        raise NotImplementedError

    @abstractmethod
    def validar_parametros(self, duracion: float) -> float:
        """Valida y devuelve la duración normalizada."""
        raise NotImplementedError

    def definir_entidad(self) -> str:
        return "Servicio"


class ServicioConsultoria(Servicio):
    """Consultoría cobrada por hora; admite duraciones de 0.5 a 8 horas."""

    def validar_parametros(self, duracion: float) -> float:
        horas = _validar_duracion_numerica(duracion)
        if not 0.5 <= horas <= 8:
            raise ValidacionError(
                "La consultoría debe durar entre 0.5 y 8 horas."
            )
        return horas

    def calcular_precio(self, duracion: float) -> float:
        return self.tarifa * self.validar_parametros(duracion)

    def describir_servicio(self) -> str:
        return "{}: consultoría por hora.".format(self.nombre)


class ServicioMantenimiento(Servicio):
    """Mantenimiento con tarifa por hora y cargo fijo de materiales."""

    def __init__(self, nombre: str, tarifa: float, cargo_materiales: float = 20.0):
        super().__init__(nombre, tarifa)
        try:
            cargo_materiales = float(cargo_materiales)
        except (TypeError, ValueError) as exc:
            LOG.exception("El cargo de materiales no es numérico.")
            raise ValidacionError(
                "El cargo de materiales debe ser un número."
            ) from exc
        if not math.isfinite(cargo_materiales) or cargo_materiales < 0:
            raise ValidacionError(
                "El cargo de materiales debe ser finito y no negativo."
            )
        self._cargo_materiales = cargo_materiales

    def validar_parametros(self, duracion: float) -> float:
        horas = _validar_duracion_numerica(duracion)
        if not 1 <= horas <= 12:
            raise ValidacionError(
                "El mantenimiento debe durar entre 1 y 12 horas."
            )
        return horas

    def calcular_precio(self, duracion: float) -> float:
        horas = self.validar_parametros(duracion)
        return self.tarifa * horas + self._cargo_materiales

    def describir_servicio(self) -> str:
        return "{}: mantenimiento por hora más materiales.".format(self.nombre)


class ServicioPaquete(Servicio):
    """Paquete con precio base que cubre hasta dos horas."""

    def validar_parametros(self, duracion: float) -> float:
        horas = _validar_duracion_numerica(duracion)
        if not 1 <= horas <= 10:
            raise ValidacionError("El paquete debe durar entre 1 y 10 horas.")
        return horas

    def calcular_precio(self, duracion: float) -> float:
        horas = self.validar_parametros(duracion)
        horas_adicionales = max(0.0, horas - 2.0)
        return self.tarifa + horas_adicionales * (self.tarifa * 0.25)

    def describir_servicio(self) -> str:
        return "{}: paquete base para las primeras 2 horas.".format(self.nombre)


class ServicioAlquiler(Servicio):
    """Alquiler de equipos con tarifa por hora, de 1 a 124 horas."""

    def validar_parametros(self, duracion: float) -> float:
        horas = _validar_duracion_numerica(duracion)
        if not 1 <= horas <= 124:
            raise ValidacionError(
                "La reserva debe durar entre 1 y 124 horas."
            )
        return horas

    def calcular_precio(self, duracion: float) -> float:
        horas = self.validar_parametros(duracion)
        return self.tarifa * horas

    def describir_servicio(self) -> str:
        return "{}: alquiler de equipos por hora.".format(self.nombre)


class ServicioAsesorias(Servicio):
    """Asesorías especializadas cobradas por hora, de 1 a 5 horas."""

    def validar_parametros(self, duracion: float) -> float:
        horas = _validar_duracion_numerica(duracion)
        if not 1 <= horas <= 5:
            raise ValidacionError(
                "La asesoría debe durar entre 1 y 5 horas."
            )
        return horas

    def calcular_precio(self, duracion: float) -> float:
        horas = self.validar_parametros(duracion)
        horas_adicionales = max(0.0, horas - 2.0)
        return self.tarifa + horas_adicionales * (self.tarifa * 0.25)

    def describir_servicio(self) -> str:
        return "{}: asesoría con tarifa base para las primeras 2 horas.".format(
            self.nombre
        )


def _validar_duracion_numerica(duracion: float) -> float:
    if isinstance(duracion, bool):
        raise ValidacionError("La duración debe ser un número.")
    try:
        horas = float(duracion)
    except (TypeError, ValueError) as exc:
        LOG.exception("La duración de un servicio no es numérica.")
        raise ValidacionError("La duración debe ser un número.") from exc
    if not math.isfinite(horas) or horas <= 0:
        raise ValidacionError(
            "La duración debe ser un número finito mayor que cero."
        )
    return horas


class EstadoReserva(Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    PROCESADA = "procesada"

class Reserva(Servicio):
    """Reserva que hereda Servicio y envuelve un servicio reservado."""
    def __init__(
        self,
        codigo: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion: float,
        estado: EstadoReserva = EstadoReserva.PENDIENTE,
    ) -> None:
        if not isinstance(cliente, Cliente):
            raise ValidacionError("La reserva requiere un objeto Cliente.")
        if not isinstance(servicio, Servicio):
            raise ValidacionError("La reserva requiere un objeto Servicio.")
        if not isinstance(estado, EstadoReserva):
            raise ValidacionError("El estado inicial de la reserva no es válido.")
        super().__init__(codigo, servicio.tarifa)
        try:
            self._duracion = servicio.validar_parametros(duracion)
        except ValidacionError as exc:
            LOG.exception("No se pudo validar la duración de la reserva %s.", codigo)
            raise ReservaError("No se pudo crear la reserva.") from exc
        self._cliente = cliente
        self._servicio = servicio
        self._estado = estado
        self._costo: Optional[float] = None

    @property
    def codigo(self) -> str:
        return self.nombre

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def duracion(self) -> float:
        return self._duracion

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    @property
    def costo(self) -> Optional[float]:
        return self._costo

    def calcular_precio(self, duracion: float) -> float:
        """Delega el cálculo al servicio asociado a la reserva."""
        duracion_validada = self.validar_parametros(duracion)
        return self._servicio.calcular_precio(duracion_validada)

    def describir_servicio(self) -> str:
        """Describe la reserva junto con el servicio que incluye."""
        return "Reserva {}: {}".format(
            self.codigo, self._servicio.describir_servicio()
        )

    def validar_parametros(self, duracion: float) -> float:
        """Delega la validación de duración al servicio asociado."""
        return self._servicio.validar_parametros(duracion)

    def confirmar(self) -> None:
        if self._estado is not EstadoReserva.PENDIENTE:
            raise EstadoReservaError(
                "Solo se puede confirmar una reserva pendiente."
            )
        self._estado = EstadoReserva.CONFIRMADA
        LOG.info("Reserva %s confirmada.", self.codigo)

    def cancelar(self) -> None:
        if self._estado not in (
            EstadoReserva.PENDIENTE,
            EstadoReserva.CONFIRMADA,
        ):
            raise EstadoReservaError(
                "Solo se puede cancelar una reserva pendiente o confirmada."
            )
        self._estado = EstadoReserva.CANCELADA
        LOG.info("Reserva %s cancelada.", self.codigo)

    def procesar(self) -> float:
        if self._estado is not EstadoReserva.CONFIRMADA:
            raise EstadoReservaError(
                "Solo se puede procesar una reserva confirmada."
            )
        try:
            self._costo = self.calcular_precio(self._duracion)
            self._estado = EstadoReserva.PROCESADA
            LOG.info(
                "Reserva %s procesada. Costo: %.2f.", self.codigo, self._costo
            )
            return self._costo
        except Exception as exc:
            LOG.exception("Error del sistema al procesar la reserva %s.", self.codigo)
            raise ReservaError(
                "Ocurrió un error al calcular el costo de la reserva."
            ) from exc

    # Aliases en español que conservan los nombres del borrador original.
    def confirmacion(self) -> None:
        self.confirmar()

    def cancelacion(self) -> None:
        self.cancelar()

    def procesamiento(self) -> float:
        return self.procesar()

    def definir_entidad(self) -> str:
        return "Reserva"

    def __str__(self) -> str:
        costo = "pendiente" if self.costo is None else "{:.2f}".format(self.costo)
        return "{} | {} | {} | {} horas | costo: {}".format(
            self.codigo,
            self.cliente.nombre,
            self.servicio.nombre,
            self.duracion,
            costo,
        )


class SistemaGestion:
    """Gestor en memoria. Los datos se pierden al cerrar el programa."""

    def __init__(self) -> None:
        self._clientes: Dict[str, Cliente] = {}
        self._servicios: Dict[str, Servicio] = {}
        self._reservas: Dict[str, Reserva] = {}
        self._contador_reservas = 1

    def registrar_cliente(
        self,
        cliente_o_nombre: Union[Cliente, str],
        cedula: Optional[str] = None,
        telefono: Optional[str] = None,
        correo_electronico: Optional[str] = None,
    ) -> Cliente:
        """Registra un Cliente o crea uno a partir de sus cuatro datos.

        Esta firma flexible ejemplifica sobrecarga por argumentos opcionales,
        ya que Python no admite dos métodos con el mismo nombre y distinta firma.
        """
        if isinstance(cliente_o_nombre, Cliente):
            if any(
                dato is not None
                for dato in (cedula, telefono, correo_electronico)
            ):
                raise ValidacionError(
                    "Pasa un Cliente o sus datos, pero no ambas formas."
                )
            cliente = cliente_o_nombre
        else:
            if not isinstance(cliente_o_nombre, str):
                raise ValidacionError("El nombre del cliente debe ser texto.")
            if None in (cedula, telefono, correo_electronico):
                raise ValidacionError(
                    "Debes proporcionar nombre, cédula, teléfono y correo."
                )
            cliente = Cliente(
                cliente_o_nombre, cedula, telefono, correo_electronico
            )

        if cliente.cedula in self._clientes:
            error = EntidadDuplicadaError(
                "Ya existe un cliente con esa cédula."
            )
            LOG.error("Intento de registrar un cliente duplicado.")
            raise error
        self._clientes[cliente.cedula] = cliente
        # No se registran cédulas, teléfonos ni correos en los logs.
        LOG.info("Cliente registrado.")
        return cliente

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        if not isinstance(servicio, Servicio):
            raise ValidacionError("Debes registrar una instancia de Servicio.")
        clave = servicio.nombre.casefold()
        if clave in self._servicios:
            raise EntidadDuplicadaError(
                "Ya existe un servicio con ese nombre."
            )
        self._servicios[clave] = servicio
        LOG.info("Servicio registrado: %s.", servicio.nombre)
        return servicio

    def crear_reserva(
        self, cliente: Cliente, servicio: Servicio, duracion: float
    ) -> Reserva:
        if not isinstance(cliente, Cliente):
            raise ValidacionError("La reserva requiere un objeto Cliente.")
        if not isinstance(servicio, Servicio):
            raise ValidacionError("La reserva requiere un objeto Servicio.")
        if cliente.cedula not in self._clientes:
            raise EntidadNoEncontradaError(
                "El cliente debe estar registrado antes de reservar."
            )
        clave_servicio = servicio.nombre.casefold()
        if clave_servicio not in self._servicios:
            raise EntidadNoEncontradaError(
                "El servicio debe estar registrado antes de reservar."
            )
        codigo = "R{:04d}".format(self._contador_reservas)
        try:
            reserva = Reserva(codigo, cliente, servicio, duracion)
        except ReservaError:
            raise
        except (TypeError, ValueError, SistemaGestionError) as exc:
            LOG.exception("No se pudo crear la reserva %s.", codigo)
            raise ReservaError("No se pudo crear la reserva.") from exc
        self._reservas[codigo] = reserva
        self._contador_reservas += 1
        LOG.info("Reserva %s creada.", codigo)
        return reserva

    def obtener_cliente(self, cedula: str) -> Cliente:
        try:
            return self._clientes[Cliente._validar_cedula(cedula)]
        except KeyError as exc:
            raise EntidadNoEncontradaError(
                "No se encontró un cliente con esa cédula."
            ) from exc
        except (TypeError, ValueError) as exc:
            raise ValidacionError("La cédula de búsqueda no es válida.") from exc

    def obtener_servicio(self, nombre: str) -> Servicio:
        try:
            return self._servicios[nombre.strip().casefold()]
        except (KeyError, AttributeError) as exc:
            raise EntidadNoEncontradaError(
                "No se encontró ese servicio."
            ) from exc

    def obtener_reserva(self, codigo: str) -> Reserva:
        try:
            return self._reservas[codigo.strip().upper()]
        except (KeyError, AttributeError) as exc:
            raise EntidadNoEncontradaError(
                "No se encontró esa reserva."
            ) from exc

    def buscar_reservas(
        self,
        codigo: Optional[str] = None,
        cliente: Optional[Cliente] = None,
    ) -> Union[Reserva, List[Reserva]]:
        """Sobrecarga práctica: búsqueda por código o filtro por cliente."""
        if codigo is not None and cliente is not None:
            raise ValidacionError(
                "Busca por código o por cliente, no por ambos a la vez."
            )
        if codigo is not None:
            return self.obtener_reserva(codigo)
        if cliente is not None:
            return [
                reserva
                for reserva in self._reservas.values()
                if reserva.cliente.cedula == cliente.cedula
            ]
        return list(self._reservas.values())


def demostrar_sistema() -> None:
    """Ejemplo de gestión y de los tres patrones de manejo de excepciones."""
    sistema = SistemaGestion()

    cliente = sistema.registrar_cliente(
        "Ana Pérez", "12345678", "+57 300 123 4567", "ana@example.com"
    )
    servicio = sistema.registrar_servicio(
        ServicioConsultoria("Asesoría", tarifa=80)
    )
    sistema.registrar_servicio(
        ServicioMantenimiento("Mantenimiento", tarifa=55, cargo_materiales=20)
    )
    sistema.registrar_servicio(ServicioPaquete("Paquete integral", tarifa=150))
    sistema.registrar_servicio(ServicioAlquiler("Alquiler de equipos", tarifa=35))
    sistema.registrar_servicio(ServicioAsesorias("Asesoría especializada", tarifa=120))

    # Ejemplo 1: try/except. Captura una búsqueda fallida y permite continuar.
    try:
        sistema.obtener_cliente("0000000000")
    except EntidadNoEncontradaError as exc:
        print("[try/except] Búsqueda controlada:", exc)

    # Ejemplo 2: try/except/else. El bloque else corre solo si no hubo error.
    try:
        servicio_encontrado = sistema.obtener_servicio(servicio.nombre)
    except EntidadNoEncontradaError as exc:
        LOG.exception("No se encontró el servicio de la demostración.")
        print("[try/except/else] Error al buscar el servicio:", exc)
    else:
        print("[try/except/else] Servicio encontrado:",
              servicio_encontrado.describir_servicio())

    reserva = sistema.crear_reserva(cliente, servicio, duracion=2)

    # Ejemplo 3: try/except/finally. El bloque finally siempre se ejecuta.
    try:
        reserva.confirmar()
        costo = reserva.procesar()
    except (SistemaGestionError, OSError) as exc:
        LOG.exception("No se pudo completar la reserva de demostración.")
        print("[try/except/finally] Error al procesar:", exc)
    else:
        print(reserva)
        print("Estado:", reserva.estado.value)
        print("Costo final: ${:.2f}".format(costo))
    finally:
        print("[try/except/finally] Fin del intento de procesamiento.")

    print("Descripción:", servicio.describir_servicio())


if __name__ == "__main__":
    try:
        demostrar_sistema()
    except SistemaGestionError as exc:
        LOG.exception("El sistema no pudo completar la demostración.")
        print("Error:", exc)
    except OSError as exc:
        LOG.exception("Error del sistema operativo.")
        print("Error del sistema operativo:", exc)
