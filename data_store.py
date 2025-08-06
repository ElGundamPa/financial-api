import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
from config import DATA_FILE, BACKUP_FILE
from logger import logger, log_data_update

class DataStore:
    def __init__(self):
        self.data = {
            "tradingview": {
                "indices": [],
                "acciones": [],
                "cripto": [],
                "forex": []
            },
            "finviz": {
                "forex": [],
                "acciones": [],
                "indices": []
            },
            "yahoo": {
                "forex": [],
                "gainers": [],
                "losers": [],
                "most_active_stocks": [],
                "most_active_etfs": [],
                "undervalued_growth": [],
                "materias_primas": [],
                "indices": []
            },
            "last_updated": None,
            "metadata": {
                "version": "1.1",
                "created_at": datetime.now().isoformat()
            }
        }
        self.load_data()

    def load_data(self) -> None:
        """Load data from file if it exists"""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Merge with default structure
                    for key in self.data.keys():
                        if key in loaded_data:
                            self.data[key] = loaded_data[key]
                    logger.info(f"📂 Datos cargados desde {DATA_FILE}")
            else:
                logger.info("📂 No se encontró archivo de datos, usando estructura por defecto")
        except Exception as e:
            logger.error(f"❌ Error cargando datos: {e}")
            # Try to load from backup
            self._load_backup()

    def _load_backup(self) -> None:
        """Load data from backup file"""
        try:
            if os.path.exists(BACKUP_FILE):
                with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    for key in self.data.keys():
                        if key in loaded_data:
                            self.data[key] = loaded_data[key]
                    logger.info(f"📂 Datos cargados desde backup {BACKUP_FILE}")
        except Exception as e:
            logger.error(f"❌ Error cargando backup: {e}")

    def save_data(self) -> None:
        """Save data to file"""
        try:
            # Create backup of current data
            if os.path.exists(DATA_FILE):
                shutil.copy2(DATA_FILE, BACKUP_FILE)
                logger.debug(f"📋 Backup creado: {BACKUP_FILE}")

            # Save new data
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug(f"💾 Datos guardados en {DATA_FILE}")
        except Exception as e:
            logger.error(f"❌ Error guardando datos: {e}")

    def update_data(self, tv: Dict[str, Any], fz: Dict[str, Any], yh: Dict[str, Any]) -> None:
        """Update data from scrapers"""
        try:
            # Validate data structure
            if not self._validate_data(tv, fz, yh):
                logger.warning("⚠️ Datos recibidos no tienen la estructura esperada")
                return

            # Update data
            self.data["tradingview"] = tv
            self.data["finviz"] = fz
            self.data["yahoo"] = yh
            self.data["last_updated"] = datetime.now().isoformat()

            # Save to file
            self.save_data()

            # Log update
            sources = []
            if tv: sources.append("TradingView")
            if fz: sources.append("Finviz")
            if yh: sources.append("Yahoo")
            
            log_data_update(sources)
            
        except Exception as e:
            logger.error(f"❌ Error actualizando datos: {e}")

    def _validate_data(self, tv: Dict, fz: Dict, yh: Dict) -> bool:
        """Validate that data has expected structure"""
        try:
            # Basic validation - check if they are dictionaries
            if not isinstance(tv, dict) or not isinstance(fz, dict) or not isinstance(yh, dict):
                return False
            
            # Check if at least one source has data
            has_data = any([
                len(tv) > 0,
                len(fz) > 0,
                len(yh) > 0
            ])
            
            return has_data
        except Exception:
            return False

    def get_data(self) -> Dict[str, Any]:
        """Get current data"""
        return self.data

    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of current data"""
        summary = {
            "last_updated": self.data.get("last_updated"),
            "sources": {}
        }
        
        for source in ["tradingview", "finviz", "yahoo"]:
            source_data = self.data.get(source, {})
            summary["sources"][source] = {
                "has_data": len(source_data) > 0,
                "sections": list(source_data.keys()) if source_data else [],
                "total_items": sum(len(section) for section in source_data.values()) if source_data else 0
            }
        
        return summary

    def clear_data(self) -> None:
        """Clear all data"""
        self.data = {
            "tradingview": {},
            "finviz": {},
            "yahoo": {},
            "last_updated": None,
            "metadata": self.data.get("metadata", {})
        }
        self.save_data()
        logger.info("🗑️ Datos limpiados")

# Global instance
data_store = DataStore()

# Convenience functions for backward compatibility
def update_data(tv, fz, yh):
    data_store.update_data(tv, fz, yh)

def get_data():
    return data_store.get_data()

def get_data_summary():
    return data_store.get_data_summary()
