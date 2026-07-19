# 💾 Storage Adapters

> [!NOTE]
> The `storage` module handles the physical and cloud-based file management of uploaded PDFs. It acts as a resilient buffer before files are vectorized.

## 🎯 Purpose and Responsibilities

To abstract away the complexities of file I/O operations and cloud SDKs, allowing the application to switch between a local on-disk cache and distributed cloud storage seamlessly based on environment configurations.

## 📄 Providers

| Provider | File | Description |
|----------|------|-------------|
| **Local Storage** | `local_storage.py` | Saves files directly to the `backend/storage/uploads/` directory. Ideal for local testing and zero-cost prototyping. |
| **Backblaze B2** | `b2_storage.py` | Highly durable cloud storage adapter using `b2sdk`. Uploads files to a Backblaze bucket and caches them locally for processing. |

## ⚙️ Service Router

The `storage_service.py` acts as the master router. Depending on the `.env` configuration, it instantly switches the active provider.

```python
# From .env
STORAGE_PROVIDER=b2 # or 'local'
```

### Internal Flow (B2 Mode)
1. **Upload:** User hits the API. `StorageService` routes the byte-stream to `B2Storage`.
2. **Cache:** The file is buffered to `backend/storage/uploads/` temporarily.
3. **Cloud Transfer:** The file is uploaded to the Backblaze B2 bucket (`RATANAI`).
4. **Cleanup:** When a document is deleted via the API, `B2Storage` removes it from both the local cache and the cloud bucket.

> [!WARNING]
> Do not bypass the `StorageService` router by importing `B2Storage` or `LocalStorage` directly in other modules. Always use `StorageService` to respect the environment configuration.
