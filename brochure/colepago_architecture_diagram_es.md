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
        B[Backend\n(FastAPI, PostgreSQL, IA)]
    end
    S((Stripe / Mercado Pago))

    P -- "Carga billetera (dinero real)\n(Conexión segura TLS)" --> S
    S -- "Confirmación de pago\n(Conexión segura TLS)" --> B
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

**Puntos clave de seguridad:**

- Todas las conexiones entre usuarios, backend y proveedores usan cifrado TLS (HTTPS).
- El backend nunca maneja dinero real, solo tokens/monedas virtuales.
- Todo el dinero real es procesado por Stripe/Mercado Pago (proveedores PCI).
- **Ni siquiera el backend tiene acceso a datos personales sensibles ni a datos de tarjetas.**
- IA biométrica protege el acceso de los niños.
- Esto garantiza máxima seguridad y privacidad para escuelas, padres y niños.
