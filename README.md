# Sistema integral de gestión de clientes y reservas
Proyecto de programación orientada a objetos para gestionar clientes, servicios 
y reservas en memoria. No utiliza bases de datos; los eventos y errores se
registran en `sistema_gestion.log`.

## Ejecución de operaciones del proyecto
Desde la carpeta del proyecto, ejecutamoos:
``` text python "Sistema integral de gestion de clientes y reservas.py" ```

La demostración ejecuta más de diez operaciones, incluyendo registros válidos e inválidos de clientes y servicios, reservas exitosas y fallidas, confirmaciones,
cancelaciones, búsquedas, errores de estado y cálculos con impuestos y descuentos.
Los errores previstos se muestran y se registran sin detener el resto de la demostración.

## Diseño
- `EntidadSistema` define el contrato abstracto común.
- `Cliente` valida y encapsula los datos personales.
- `Servicio` y sus clases derivadas implementan servicios de salas, alquiler de equipos, asesorías, consultoría, mantenimiento y paquetes.
- `Reserva` integra cliente, servicio, duración y estado, y procesa su costo.
- `SistemaGestion` mantiene las colecciones en memoria.
- Las excepciones personalizadas se registran en el archivo de log y se encadenan
cuando una excepción de bajo nivel se transforma en un error del sistema.

El cálculo del costo admite porcentajes opcionales de impuesto y descuento. El
descuento se aplica antes del impuesto; ambos valores deben estar entre 0 y 100.
