"""
Schema Pydantic per validazione bandi appalto
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime


class CategoriaLavori(BaseModel):
    """Categoria SOA richiesta per lavori"""
    categoria: str = Field(description="Es. OG1, OS30, OG3")
    classifica: str = Field(description="Classifica I-VIII")
    importo: float = Field(gt=0, description="Importo in euro")
    tipo: Literal["prevalente", "scorporabile"] = Field(description="Tipo categoria")
    sios: bool = Field(default=False, description="Sistema di qualificazione obbligatorio")
    subappalto_max_perc: int = Field(ge=0, le=100, description="% max subappalto")
    avvalimento: bool = Field(default=True, description="Avvalimento consentito")
    
    @validator('categoria')
    def normalize_categoria(cls, v):
        """Normalizza categoria (OG 1 → OG1)"""
        return v.replace(' ', '').upper()


class Importi(BaseModel):
    """Importi del bando"""
    totale_appalto: float = Field(gt=0)
    lavori: Optional[float] = Field(default=None, gt=0)
    sicurezza: Optional[float] = Field(default=None, ge=0)
    manodopera: Optional[float] = Field(default=None, ge=0)
    progettazione: Optional[float] = Field(default=None, ge=0)
    ribassabile: Optional[float] = Field(default=None, gt=0)


class Localizzazione(BaseModel):
    """Localizzazione intervento"""
    regione: Optional[str]
    provincia: Optional[str]
    comune: Optional[str]
    indirizzo: Optional[str]


class Procedura(BaseModel):
    """Dettagli procedura"""
    tipo: str = Field(description="Es. procedura aperta, negoziata")
    criterio: str = Field(description="Es. prezzo più basso, OEPV")
    esclusione_automatica: bool = Field(default=False)
    metodo_anomalia: Optional[str]
    scadenza: Optional[str]


class BandoStrutturato(BaseModel):
    """Schema completo bando appalto pubblico"""
    
    # Metadati
    tipo: Literal["bando_lavori", "bando_servizi", "bando_forniture"] = "bando_lavori"
    fonte: str
    cig: Optional[str] = Field(default=None, pattern=r'^[A-Z0-9]{10}$')
    cup: Optional[str] = Field(default=None, pattern=r'^[A-Z][0-9]{2}[A-Z][0-9]{11}$')
    pnrr: bool = Field(default=False)
    
    # Oggetto
    oggetto: str
    
    # Dati economici
    importi: Importi
    
    # Requisiti
    categorie: List[CategoriaLavori]
    
    # Localizzazione
    localizzazione: Localizzazione
    
    # Procedura
    procedura: Procedura
    
    # Metadata estrazione
    confidence_score: Optional[str] = Field(default="medium")
    extracted_at: datetime = Field(default_factory=datetime.now)
    
    @validator('categorie')
    def check_categorie_importi(cls, v, values):
        """Verifica coerenza importi categorie"""
        if 'importi' in values and values['importi'].lavori:
            somma_cat = sum(c.importo for c in v)
            diff = abs(somma_cat - values['importi'].lavori)
            
            # Warning se differenza > 1%
            if diff > values['importi'].lavori * 0.01:
                print(f"⚠️  Discrepanza importi categorie: {somma_cat:.2f} vs {values['importi'].lavori:.2f}")
        
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


if __name__ == "__main__":
    # Test schema
    bando_test = BandoStrutturato(
        fonte="SUA Roma",
        cig="A004AF8E8C",
        pnrr=True,
        oggetto="Test bando",
        importi=Importi(
            totale_appalto=714685.46,
            lavori=693820.49,
            sicurezza=18610.83
        ),
        categorie=[
            CategoriaLavori(
                categoria="OG1",
                classifica="II",
                importo=468930.98,
                tipo="prevalente",
                subappalto_max_perc=40
            )
        ],
        localizzazione=Localizzazione(
            regione="Lazio",
            provincia="Roma"
        ),
        procedura=Procedura(
            tipo="procedura aperta",
            criterio="prezzo più basso"
        )
    )
    
    print("\n✅ Schema validato:")
    print(bando_test.json(indent=2, ensure_ascii=False))