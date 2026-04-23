# ColePago/StudentWallet – Billetera Digital Segura para Escuelas

---

![Logo ColePago](https://dummyimage.com/120x60/4e73df/ffffff&text=ColePago)

## ¿Cómo Funciona?

### 1. Los padres cargan la billetera
![Recarga Padres](https://dummyimage.com/100x80/6c757d/ffffff&text=Padres+Cargan)
- El padre usa la app para cargar dinero a través de Stripe/Mercado Pago.
- **Ningún dato de tarjeta ni dinero real pasa por nuestro backend.**

### 2. Se acreditan tokens virtuales
![Tokens](https://dummyimage.com/80x80/36b37e/ffffff&text=Tokens)
- El backend recibe la confirmación del pago y acredita tokens/monedas virtuales a la billetera del niño.
- Solo tokens/monedas fluyen por el backend.

### 3. El niño gasta en la escuela
![Niño Paga](https://dummyimage.com/100x80/f6c23e/ffffff&text=Ni%C3%B1o+Paga)
- El niño usa tokens para pagar en la cantina, tienda o actividades escolares.
- El padre recibe notificación instantánea.

### 4. Seguridad y Protección
![Seguridad](https://dummyimage.com/80x80/1cc88a/ffffff&text=Seguro)
- **IA: Detección facial y biometría:** Solo el niño autorizado accede a la billetera.
- **Sin exposición de dinero real:** Todo el dinero real es gestionado por proveedores PCI (Stripe/Mercado Pago).
- **Privacidad:** No se almacenan datos sensibles de pago en la app ni en el backend.

---

**ColePago/StudentWallet** – Seguro, inteligente y simple para familias y escuelas.

**Modelo de negocio:**
- ColePago obtiene una ganancia del 2% sobre cada transacción monetaria entrante (recarga de billetera).

Contacto: [tu-email@ejemplo.com]

© 2026 ColePago
# ColePago/StudentWallet – Diagrama de Arquitectura Segura

![Logo ColePago](https://dummyimage.com/120x60/4e73df/ffffff&text=ColePago)

```mermaid
flowchart LR
    subgraph Padres
        P[Padres]
    end
    subgraph Niños
        K[Niños]
    end
    subgraph Comerciantes
        M[Comerciantes]
    end
    subgraph Backend
        B[Backend]
    end
    S((Stripe / Mercado Pago))

    P -- "Carga billetera (dinero real)" --> S
    S -- "Confirmación de pago" --> B
    B -- "Acredita tokens" --> K
    K -- "Gasta tokens" --> M
    M -- "Registro de transacción" --> B
    B -- "Notificaciones, control" --> P
    B -- "Sin dinero real, solo tokens" --- K
    B -- "Sin dinero real, solo tokens" --- M
    S -. "El backend nunca maneja dinero real" .- B

    classDef highlight fill:#f9f,stroke:#333,stroke-width:2px;
    class B highlight;
```

---

**Punto clave de seguridad:**
- El backend nunca maneja dinero real, solo tokens/monedas virtuales.
- Todo el dinero real es procesado por Stripe/Mercado Pago (proveedores PCI).
- Esto garantiza máxima seguridad para escuelas, padres y niños.
