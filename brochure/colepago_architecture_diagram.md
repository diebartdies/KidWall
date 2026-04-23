# ColePago/StudentWallet – Secure Architecture Diagram

![ColePago Logo](https://dummyimage.com/120x60/4e73df/ffffff&text=ColePago)

```mermaid
flowchart LR
    subgraph Parents
        P[Parents]
    end
    subgraph Kids
        K[Kids]
    end
    subgraph Merchants
        M[Merchants]
    end
    subgraph Backend
        B[Backend]
    end
    S((Stripe / Mercado Pago))

    P -- "Fund Wallet (real money)" --> S
    S -- "Payment Confirmation" --> B
    B -- "Credit Tokens" --> K
    K -- "Spend Tokens" --> M
    M -- "Transaction Log" --> B
    B -- "Notifications, Controls" --> P
    B -- "No real money, only tokens" --- K
    B -- "No real money, only tokens" --- M
    S -. "No real money ever in backend" .- B

    classDef highlight fill:#f9f,stroke:#333,stroke-width:2px;
    class B highlight;
```

---

**Key Security Highlight:**

- The backend never handles real money—only virtual tokens/coins.
- All real money is processed by Stripe/Mercado Pago (PCI-compliant providers).
- This ensures maximum safety for schools, parents, and kids.
