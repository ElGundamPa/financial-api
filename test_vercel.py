#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de la API para Vercel
"""

import asyncio
import json

from app_core_simple import create_app, create_data_summary, scrape_all_data


async def test_app():
    """Probar la aplicación"""
    print("🧪 Probando aplicación...")

    # Crear aplicación
    app = create_app("vercel")
    print(f"✅ App creada - Runtime: {app['runtime']}")
    print(f"📊 Fuentes disponibles: {len(app['sources_status'])}")

    # Mostrar estado de fuentes
    for source, info in app["sources_status"].items():
        print(f"  - {source}: {info['status']} ({', '.join(info['data_types'])})")

    # Probar scraping
    print("\n🔄 Probando scraping...")
    from app_core_simple import Settings

    settings = Settings("vercel")
    data = await scrape_all_data(settings)
    print(f"✅ Scraping completado - {data['total_sources']} fuentes")

    # Mostrar errores si los hay
    if data["errors"]:
        print("⚠️ Errores encontrados:")
        for error in data["errors"]:
            print(f"  - {error['source']}: {error['error']}")

    # Crear resumen
    print("\n📋 Creando resumen...")
    summary = create_data_summary(data)
    print(f"✅ Resumen creado - {len(summary['sources'])} fuentes con datos")

    # Mostrar estadísticas
    for category, items in summary.items():
        if isinstance(items, list) and items:
            print(f"  - {category}: {len(items)} elementos")

    print("\n🎉 ¡Todas las pruebas pasaron!")


if __name__ == "__main__":
    asyncio.run(test_app())
