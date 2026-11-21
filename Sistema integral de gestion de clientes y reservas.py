#Sistema integral de gestion de clientes y reservas
#Brayan David Martinez Rincon
#Fase 4 Programacion
from abc import ABC, abstractmethod
from enum import Enum
import logging
import math
import re
from typing import Dict, List, Optional, Union

#Archivo de logs con los errores registrados
def configurar_logs() -> logging.Logger:
    """Configura el registro en archivo y usa consola si el archivo no se puede abrir."""
    logger = logging.getLogger("sistema_gestion")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    formato = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    try:
        archivo = logging.FileHandler("sistema_gestion.log", encoding="utf-8")
        archivo.setFormatter(formato)
        logger.addHandler(archivo)
    except OSError as exc:
        consola = logging.StreamHandler()
        consola.setFormatter(formato)
        logger.addHandler(consola)
        logger.exception("No se pudo abrir el archivo de logs; se usará la consola.")
    return logger
LOG = configurar_logs()

# Excepciones personalizadas
class SistemaGestionError(Exception):
    """Excepción base del sistema."""

    def __init__(self, mensaje: str) -> None:
        LOG.error("%s: %s", type(self).__name__, mensaje)
        super().__init__(mensaje)

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

#Clase Abstracta Entidad del Sistema
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

#Clase Cliente 
class Cliente(EntidadSistema):
    """Cliente con datos personales validados y encapsulados."""
    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    def __init__(
        self,
        nombre: str,
        cedula: Union[str, int],
        telefono: Union[str, int],
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

#validacion de cedula
    @staticmethod
    def _validar_cedula(cedula: Union[str, int]) -> str:
        if not isinstance(cedula, (str, int)):
            raise TypeError("La cédula debe ser texto o un número entero.")
        limpia = re.sub(r"[\s.-]", "", str(cedula))
        if not limpia.isdigit() or not 5 <= len(limpia) <= 10:
            raise ValueError("La cédula debe contener entre 5 y 10 dígitos.")
        return limpia

#validacion de telefono
    @staticmethod
    def _validar_telefono(telefono: Union[str, int]) -> str:
        if not isinstance(telefono, (str, int)):
            raise TypeError("El teléfono debe ser texto o un número entero.")
        limpia = re.sub(r"[\s()+.-]", "", str(telefono))
        if not limpia.isdigit() or not 7 <= len(limpia) <= 15:
            raise ValueError("El teléfono debe contener entre 7 y 15 dígitos.")
        return limpia

#validacion de correo
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

#Clase abstracta servicio
class Servicio(EntidadSistema, ABC):
    """Clase abstracta para servicios con cálculo y validación polimórficos."""
    def __init__(self, nombre: str, tarifa: float) -> None:
        super().__init__(nombre)
        try:
            if isinstance(tarifa, bool):
                raise TypeError("La tarifa no puede ser un valor booleano.")
            tarifa = float(tarifa)
        except (TypeError, ValueError) as exc:
            LOG.exception("La tarifa del servicio no es numérica.")
            raise ValidacionError("La tarifa debe ser un número.") from exc
        if not math.isfinite(tarifa) or tarifa <= 0:
            raise ValidacionError("La tarifa debe ser un número finito mayor que cero.")
        self._tarifa = tarifa

#tarifa por servicio
    @property
    def tarifa(self) -> float:
        return self._tarifa

#precio por duracion del servicio
    @abstractmethod
    def calcular_precio(
        self, duracion: float, impuesto: float = 0.0, descuento: float = 0.0
    ) -> float:
        """Calcula el costo con porcentajes opcionales de impuesto y descuento."""
        raise NotImplementedError

#descripcion del servicio
    @abstractmethod
    def describir_servicio(self) -> str:
        """Describe el servicio para el usuario."""
        raise NotImplementedError

#validacion de parametros
    @abstractmethod
    def validar_parametros(self, duracion: float) -> float:
        """Valida y devuelve la duración normalizada."""
        raise NotImplementedError

#definicion de entidad
    def definir_entidad(self) -> str:
        return "Servicio"

#clase servicio consultoria
class ServicioConsultoria(Servicio):
    """Consultoría cobrada por hora; admite duraciones de 1 a 8 horas."""
    def validar_parametros(self, duracion: float) -> float:
        horas = _validar_duracion_numerica(duracion)
        if not 1 <= horas <= 8:
            raise ValidacionError("La consultoría debe durar entre 1 y 8 horas.")
        return horas

    def calcular_precio(
        self, duracion: float, impuesto: float = 0.0, descuento: float = 0.0
    ) -> float:
        subtotal = self.tarifa * self.validar_parametros(duracion)
        return _aplicar_impuestos_descuento(subtotal, impuesto, descuento)

    def describir_servicio(self) -> str:
        return "{}: consultoría por hora.".format(self.nombre)

#Clase Servicio de Mantenimiento de equipos
class ServicioMantenimiento(Servicio):
    """Mantenimiento con tarifa por hora y cargo fijo de materiales."""

    def __init__(self, nombre: str, tarifa: float, cargo_materiales: float = 20.0):
        super().__init__(nombre, tarifa)
        try:
            if isinstance(cargo_materiales, bool):
                raise TypeError("El cargo no puede ser un valor booleano.")
            cargo_materiales = float(cargo_materiales)
        except (TypeError, ValueError) as exc:
            LOG.exception("El cargo de materiales no es numérico.")
            raise ValidacionError("El cargo de materiales debe ser un número.") from exc
        if not math.isfinite(cargo_materiales) or cargo_materiales < 0:
            raise ValidacionError("El cargo de materiales debe ser finito y no negativo.")
        self._cargo_materiales = cargo_materiales

    def validar_parametros(self, duracion: float) -> float:
        horas = _validar_duracion_numerica(duracion)
        if not 1 <= horas <= 12:
            raise ValidacionError("El mantenimiento debe durar entre 1 y 12 horas.")
        return horas

    def calcular_precio(
        self, duracion: float, impuesto: float = 0.0, descuento: float = 0.0
    ) -> float:
        horas = self.validar_parametros(duracion)
        subtotal = self.tarifa * horas + self._cargo_materiales
        return _aplicar_impuestos_descuento(subtotal, impuesto, descuento)

    def describir_servicio(self) -> str:
        return "{}: mantenimiento por hora más materiales.".format(self.nombre)

#Clase servicio de paquete
class ServicioPaquete(Servicio):
    """Paquete con precio base que cubre hasta dos horas."""

    def validar_parametros(self, duracion: float) -> float:
        horas = _validar_duracion_numerica(duracion)
        if not 1 <= horas <= 10:
            raise ValidacionError("El paquete debe durar entre 1 y 10 horas.")
        return horas

    def calcular_precio(
        self, duracion: float, impuesto: float = 0.0, descuento: float = 0.0
    ) -> float:
        horas = self.validar_parametros(duracion)
        horas_adicionales = max(0.0, horas - 2.0)
        subtotal = self.tarifa + horas_adicionales * (self.tarifa * 0.25)
        return _aplicar_impuestos_descuento(subtotal, impuesto, descuento)

    def describir_servicio(self) -> str:
        return "{}: paquete base para las primeras 2 horas.".format(self.nombre)

#clase servicio reserva de salas
class ServicioReservaSalas(Servicio):
    """Reserva de salas con tarifa por hora, de 1 a 12 horas."""

    def validar_parametros(self, duracion: float) -> float:
        horas = _validar_duracion_numerica(duracion)
        if not 1 <= horas <= 12:
            raise ValidacionError("La reserva debe durar entre 1 y 12 horas.")
        return horas

    def calcular_precio(
        self, duracion: float, impuesto: float = 0.0, descuento: float = 0.0
    ) -> float:
        horas = self.validar_parametros(duracion)
        subtotal = self.tarifa * horas
        return _aplicar_impuestos_descuento(subtotal, impuesto, descuento)

    def describir_servicio(self) -> str:
        return "{}: reserva de salas por hora.".format(self.nombre)

#Clase servicio de alquiler
class ServicioAlquiler(Servicio):
    """Alquiler de equipos con tarifa por hora, de 1 a 124 horas."""

    def validar_parametros(self, duracion: float) -> float:
        horas = _validar_duracion_numerica(duracion)
        if not 1 <= horas <= 124:
            raise ValidacionError("La reserva debe durar entre 1 y 124 horas.")
        return horas

    def calcular_precio(
        self, duracion: float, impuesto: float = 0.0, descuento: float = 0.0
    ) -> float:
        horas = self.validar_parametros(duracion)
        subtotal = self.tarifa * horas
        return _aplicar_impuestos_descuento(subtotal, impuesto, descuento)

    def describir_servicio(self) -> str:
        return "{}: alquiler de equipos por hora.".format(self.nombre)

#Clase servicio de asesorias
class ServicioAsesorias(Servicio):
    """Asesorías especializadas cobradas por hora, de 1 a 5 horas."""

    def validar_parametros(self, duracion: float) -> float:
        horas = _validar_duracion_numerica(duracion)
        if not 1 <= horas <= 5:
            raise ValidacionError("La asesoría debe durar entre 1 y 5 horas.")
        return horas

    def calcular_precio(
        self, duracion: float, impuesto: float = 0.0, descuento: float = 0.0
    ) -> float:
        horas = self.validar_parametros(duracion)
        horas_adicionales = max(0.0, horas - 2.0)
        subtotal = self.tarifa + horas_adicionales * (self.tarifa * 0.25)
        return _aplicar_impuestos_descuento(subtotal, impuesto, descuento)

    def describir_servicio(self) -> str:
        return "{}: asesoría con tarifa base para las primeras 2 horas.".format(self.nombre)

def _validar_duracion_numerica(duracion: float) -> float:
    if isinstance(duracion, bool):
        raise ValidacionError("La duración debe ser un número.")
    try:
        horas = float(duracion)
    except (TypeError, ValueError) as exc:
        LOG.exception("La duración de un servicio no es numérica.")
        raise ValidacionError("La duración debe ser un número.") from exc
    if not math.isfinite(horas) or horas <= 0:
        raise ValidacionError("La duración debe ser un número finito mayor que cero.")
    return horas


def _aplicar_impuestos_descuento(
    subtotal: float, impuesto: float, descuento: float
) -> float:
    """Aplica descuento antes del impuesto; ambos porcentajes van de 0 a 100."""
    porcentajes = []
    for nombre, valor in (("impuesto", impuesto), ("descuento", descuento)):
        if isinstance(valor, bool):
            raise ValidacionError("El {} debe ser un porcentaje numérico.".format(nombre))
        try:
            porcentaje = float(valor)
        except (TypeError, ValueError) as exc:
            raise ValidacionError(
                "El {} debe ser un porcentaje numérico.".format(nombre)
            ) from exc
        if not math.isfinite(porcentaje) or not 0 <= porcentaje <= 100:
            raise ValidacionError(
                "El {} debe estar entre 0 y 100.".format(nombre.capitalize())
            )
        porcentajes.append(porcentaje)
    impuesto_validado, descuento_validado = porcentajes
    return subtotal * (1 - descuento_validado / 100) * (1 + impuesto_validado / 100)


#Clase estado de reserva
class EstadoReserva(Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    PROCESADA = "procesada"

#Clase reserva
class Reserva(EntidadSistema):
    """Reserva que integra un cliente con el servicio que ha solicitado."""
    def __init__(self, codigo: str, cliente: Cliente, servicio: Servicio, duracion: float,
    estado: EstadoReserva = EstadoReserva.PENDIENTE,) -> None:
        if not isinstance(cliente, Cliente):
            raise ValidacionError("La reserva requiere un objeto Cliente.")
        if not isinstance(servicio, Servicio):
            raise ValidacionError("La reserva requiere un objeto Servicio.")
        if not isinstance(estado, EstadoReserva):
            raise ValidacionError("El estado inicial de la reserva no es válido.")
        super().__init__(codigo)
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

    def calcular_precio(
        self, duracion: float, impuesto: float = 0.0, descuento: float = 0.0
    ) -> float:
        """Delega el cálculo al servicio asociado a la reserva."""
        duracion_validada = self.validar_parametros(duracion)
        return self._servicio.calcular_precio(
            duracion_validada, impuesto=impuesto, descuento=descuento
        )

    def describir_servicio(self) -> str:
        """Describe la reserva junto con el servicio que incluye."""
        return "Reserva {}: {}".format(
            self.codigo, self._servicio.describir_servicio())

    def validar_parametros(self, duracion: float) -> float:
        """Delega la validación de duración al servicio asociado."""
        return self._servicio.validar_parametros(duracion)

#confirmacion de reserva
    def confirmar(self) -> None:
        if self._estado is not EstadoReserva.PENDIENTE:
            raise EstadoReservaError("Solo se puede confirmar una reserva pendiente.")
        self._estado = EstadoReserva.CONFIRMADA
        LOG.info("Reserva %s confirmada.", self.codigo)

#cancelacion de reserva
    def cancelar(self) -> None:
        if self._estado not in (EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA,):
            raise EstadoReservaError("Solo se puede cancelar una reserva pendiente o confirmada.")
        self._estado = EstadoReserva.CANCELADA
        LOG.info("Reserva %s cancelada.", self.codigo)

#procesar reserva
    def procesar(self, impuesto: float = 0.0, descuento: float = 0.0) -> float:
        if self._estado is not EstadoReserva.CONFIRMADA:
            raise EstadoReservaError("Solo se puede procesar una reserva confirmada.")
        try:
            self._costo = self.calcular_precio(self._duracion, impuesto=impuesto, descuento=descuento)
            self._estado = EstadoReserva.PROCESADA
            LOG.info("Reserva %s procesada. Costo: %.2f.", self.codigo, self._costo)
            return self._costo
        except Exception as exc:
            LOG.exception("Error del sistema al procesar la reserva %s.", self.codigo)
            raise ReservaError("Ocurrió un error al calcular el costo de la reserva.") from exc

    def confirmacion(self) -> None:
        self.confirmar()

    def cancelacion(self) -> None:
        self.cancelar()

    def procesamiento(self, impuesto: float = 0.0, descuento: float = 0.0) -> float:
        return self.procesar(impuesto=impuesto, descuento=descuento)

    def definir_entidad(self) -> str:
        return "Reserva"

    def __str__(self) -> str:
        costo = "pendiente" if self.costo is None else "{:.2f}".format(self.costo)
        return "{} | {} | {} | {} horas | costo: {}".format(
            self.codigo, self.cliente.nombre, self.servicio.nombre, self.duracion, costo,)

#clase sistema de gestion de datos
class SistemaGestion:
    """Gestor en memoria. Los datos se pierden al cerrar el programa."""

    def __init__(self) -> None:
        self._clientes: Dict[str, Cliente] = {}
        self._servicios: Dict[str, Servicio] = {}
        self._reservas: Dict[str, Reserva] = {}
        self._contador_reservas = 1

    def registrar_cliente(self, cliente_o_nombre: Union[Cliente, str], cedula: Optional[Union[str, int]] = None,
        telefono: Optional[Union[str, int]] = None, correo_electronico: Optional[str] = None,) -> Cliente:
        if isinstance(cliente_o_nombre, Cliente):
            if any(dato is not None for dato in (cedula, telefono, correo_electronico)):
                raise ValidacionError("Pasa un Cliente o sus datos, pero no ambas formas.")
            cliente = cliente_o_nombre
        else:
            if not isinstance(cliente_o_nombre, str):
                raise ValidacionError("El nombre del cliente debe ser texto.")
            if None in (cedula, telefono, correo_electronico):
                raise ValidacionError("Debes proporcionar nombre, cédula, teléfono y correo.")
            cliente = Cliente(cliente_o_nombre, cedula, telefono, correo_electronico)
        if cliente.cedula in self._clientes:
            error = EntidadDuplicadaError("Ya existe un cliente con esa cédula.")
            raise error
        self._clientes[cliente.cedula] = cliente
        LOG.info("Cliente registrado.")
        return cliente

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        if not isinstance(servicio, Servicio):
            raise ValidacionError("Debes registrar una instancia de Servicio.")
        clave = servicio.nombre.casefold()
        if clave in self._servicios:
            raise EntidadDuplicadaError("Ya existe un servicio con ese nombre.")
        self._servicios[clave] = servicio
        LOG.info("Servicio registrado: %s.", servicio.nombre)
        return servicio

    def crear_reserva(self, cliente: Cliente, servicio: Servicio, duracion: float) -> Reserva:
        if not isinstance(cliente, Cliente):
            raise ValidacionError("La reserva requiere un objeto Cliente.")
        if not isinstance(servicio, Servicio):
            raise ValidacionError("La reserva requiere un objeto Servicio.")
        if self._clientes.get(cliente.cedula) is not cliente:
            raise EntidadNoEncontradaError("El cliente debe estar registrado antes de reservar.")
        clave_servicio = servicio.nombre.casefold()
        if self._servicios.get(clave_servicio) is not servicio:
            raise EntidadNoEncontradaError("El servicio debe estar registrado antes de reservar.")
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

    def obtener_cliente(self, cedula: Union[str, int]) -> Cliente:
        try:
            return self._clientes[Cliente._validar_cedula(cedula)]
        except KeyError as exc:
            raise EntidadNoEncontradaError("No se encontró un cliente con esa cédula.") from exc
        except (TypeError, ValueError) as exc:
            raise ValidacionError("La cédula de búsqueda no es válida.") from exc

    def obtener_servicio(self, nombre: str) -> Servicio:
        try:
            return self._servicios[nombre.strip().casefold()]
        except (KeyError, AttributeError) as exc:
            raise EntidadNoEncontradaError("No se encontró ese servicio.") from exc

    def obtener_reserva(self, codigo: str) -> Reserva:
        try:
            return self._reservas[codigo.strip().upper()]
        except (KeyError, AttributeError) as exc:
            raise EntidadNoEncontradaError("No se encontró esa reserva.") from exc

    def buscar_reservas(self, codigo: Optional[str] = None, 
        cliente: Optional[Cliente] = None,)-> Union[Reserva, List[Reserva]]:
        """Sobrecarga práctica: búsqueda por código o filtro por cliente."""
        if codigo is not None and cliente is not None:
            raise ValidacionError("Busca por código o por cliente, no por ambos a la vez.")
        if codigo is not None:
            return self.obtener_reserva(codigo)
        if cliente is not None:
            if not isinstance(cliente, Cliente):
                raise ValidacionError("El cliente de búsqueda no es válido.")
            return [
                reserva
                for reserva in self._reservas.values()
                if reserva.cliente.cedula == cliente.cedula
            ]
        return list(self._reservas.values())

#demostracion de funcionalidad del sistema
def demostrar_sistema() -> None:
    """Ejecuta escenarios válidos e inválidos y continúa tras los errores previstos."""
    sistema = SistemaGestion()
    operaciones = [0]

    def operar(nombre: str, accion):
        operaciones[0] += 1
        numero = operaciones[0]
        LOG.info("Inicio de operación %02d: %s.", numero, nombre)
        try:
            return accion()
        finally:
            LOG.info("Fin de operación %02d: %s.", numero, nombre)
    cliente = operar("registro válido de cliente",
        lambda: sistema.registrar_cliente("Marcela Alejandra Diaz", "1053654976", "+57 315 140 4210", "marcelaperz@gmail.com"),)
    try:
        operar("registro inválido de cliente",
            lambda: sistema.registrar_cliente("Cliente inválido", "abc123", "3001234567", "correo-invalido"),)
    except ValidacionError as exc:
        print("[try/except] Registro inválido controlado:", exc)
    try:
        operar("registro duplicado de cliente", lambda: sistema.registrar_cliente(
                "Otro nombre", cliente.cedula, "3123343426", "Juliandbmarin@hotmail.com"),)
    except EntidadDuplicadaError as exc:
        print("[try/except/else] Duplicado controlado:", exc)
    else:
        raise AssertionError("El sistema aceptó un cliente duplicado.")
    sala = operar("registro de servicio de salas", lambda: sistema.registrar_servicio(ServicioReservaSalas("Sala principal", 45)),)
    consultoria = operar("registro de servicio de asesoría",
        lambda: sistema.registrar_servicio(ServicioConsultoria("Consultoría", 80)),)

    try:
        operar("creación de servicio con tarifa inválida", lambda: sistema.registrar_servicio(ServicioConsultoria("Servicio inválido", -50)),)
    except ValidacionError as exc:
        print("Creación inválida de servicio controlada:", exc)

    try:
        operar("registro de un objeto que no es servicio", lambda: sistema.registrar_servicio(object()),)
    except ValidacionError as exc:
        print("Tipo de servicio inválido controlado:", exc)

    try:
        operar("reserva con duración inválida", lambda: sistema.crear_reserva(cliente, consultoria, duracion=99),)
    except ReservaError as exc:
        print("Reserva fallida controlada:", exc)

    try:
        operar("reserva de servicio no registrado", lambda: sistema.crear_reserva(cliente, ServicioAlquiler("Equipo no registrado", 25), duracion=2),)
    except EntidadNoEncontradaError as exc:
        print("Servicio no disponible controlado:", exc)

    reserva = operar("creación de reserva válida", lambda: sistema.crear_reserva(cliente, consultoria, duracion=2),)
    operar("confirmación de reserva", reserva.confirmar)

    try:
        costo = operar("procesamiento con descuento e impuesto", lambda: reserva.procesar(impuesto=19, descuento=10),)
    except SistemaGestionError as exc:
        LOG.exception("No se pudo procesar la reserva de demostración.")
        print("[try/except/finally] Error controlado:", exc)
        raise
    else:
        print(reserva)
        print("Estado:", reserva.estado.value)
        print("Costo con descuento e impuesto: ${:.2f}".format(costo))
    finally:
        print("[try/except/finally] Fin del intento de procesamiento.")

    operar("búsqueda de reserva por código", lambda: sistema.buscar_reservas(codigo=reserva.codigo),)
    operar("búsqueda de reservas por cliente", lambda: sistema.buscar_reservas(cliente=cliente),)

    try:
        operar("intento de reprocesar reserva", reserva.procesar)
    except EstadoReservaError as exc:
        print("Transición de estado inválida controlada:", exc)

    reserva_sala = operar("creación de reserva de sala", lambda: sistema.crear_reserva(cliente, sala, duracion=2),)
    operar("cancelación de reserva pendiente", reserva_sala.cancelar)

    try:
        operar("intento de cancelar reserva ya cancelada", reserva_sala.cancelar)
    except EstadoReservaError as exc:
        print("Cancelación inválida controlada:", exc)

    reserva_cancelada = operar("creación de reserva para cancelación confirmada", lambda: sistema.crear_reserva(cliente, sala, duracion=1),)
    operar("confirmación antes de cancelar", reserva_cancelada.confirmar)
    operar("cancelación de reserva confirmada", reserva_cancelada.cancelar)

    try:
        operar("cálculo con porcentaje inválido", lambda: consultoria.calcular_precio(1, impuesto=150))
    except ValidacionError as exc:
        print("Porcentaje inválido controlado:", exc)

    print("Operaciones simuladas:", operaciones[0])
    print("El sistema continuó funcionando después de los errores controlados.")

if __name__ == "__main__":
    try:
        demostrar_sistema()
    except SistemaGestionError as exc:
        LOG.exception("El sistema no pudo completar la demostración.")
        print("Error del sistema:", exc)
    except OSError as exc:
        LOG.exception("Error del sistema operativo.")
        print("Error del sistema operativo:", exc)