from fastapi import FastAPI, Query, HTTPException
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import products 
app = FastAPI(
    title="Мебельный магазин API",
    description="API для управления каталогом мебели с хранением в JSON",
    version="2.0"
)

# Модели для валидации данных
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Название товара")
    type: str = Field(..., min_length=1, description="Тип мебели")
    material: str = Field(..., min_length=1, description="Материал")
    price: float = Field(..., gt=0, description="Цена товара")

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, description="Название товара")
    type: Optional[str] = Field(None, min_length=1, description="Тип мебели")
    material: Optional[str] = Field(None, min_length=1, description="Материал")
    price: Optional[float] = Field(None, gt=0, description="Цена товара")

def sort_products(product_list: list, sort_by: str = "name", order: str = "asc"):
    """
    Сортировка списка товаров
    
    Args:
        product_list: список товаров
        sort_by: поле для сортировки (name, type, material, price)
        order: порядок сортировки (asc - по возрастанию, desc - по убыванию)
    """
    reverse = order.lower() == "desc"
    
    if sort_by not in ["name", "type", "material", "price"]:
        sort_by = "name"
    
    return sorted(product_list, key=lambda x: x[sort_by], reverse=reverse)

@app.get("/")
def root():
    return {
        "message": "Добро пожаловать в API мебельного магазина!",
        "endpoints": {
            "GET /products": "Получить все товары (сортировка: ?sort=asc/desc)",
            "GET /products/{id}": "Получить товар по ID",
            "POST /products": "Создать новый товар",
            "PUT /products/{id}": "Обновить товар",
            "DELETE /products/{id}": "Удалить товар",
            "GET /products/types": "Получить все типы мебели",
            "GET /products/statistics": "Получить статистику",
            "GET /products/search": "Расширенный поиск"
        }
    }

@app.get("/products")
def get_products(
    type: Optional[str] = Query(None, description="Фильтр по типу мебели"),
    sort: Optional[str] = Query("asc", description="Сортировка: asc (А-Я) или desc (Я-А)", regex="^(asc|desc)$"),
    sort_by: Optional[str] = Query("name", description="Поле для сортировки: name, type, material, price")
):
    """
    Получить список всех товаров с возможностью фильтрации по типу и сортировки
    """
    if type:
        result = products.get_products_by_type(type)
    else:
        result = products.get_all_products()
    
    # Применяем сортировку
    result = sort_products(result, sort_by, sort)
    
    return {
        "count": len(result),
        "products": result,
        "sorting": {
            "field": sort_by,
            "order": sort
        },
        "filter": {"type": type} if type else None
    }

@app.get("/products/types")
def get_types():
    """Получить все уникальные типы мебели"""
    return {
        "types": products.get_unique_types(),
        "count": len(products.get_unique_types())
    }

@app.get("/products/statistics")
def get_statistics():
    """Получить статистику по каталогу"""
    return products.get_statistics()

@app.get("/products/search")
def search_products_endpoint(
    name: Optional[str] = Query(None, description="Поиск по названию"),
    type: Optional[str] = Query(None, description="Фильтр по типу"),
    min_price: Optional[float] = Query(None, ge=0, description="Минимальная цена"),
    max_price: Optional[float] = Query(None, ge=0, description="Максимальная цена"),
    material: Optional[str] = Query(None, description="Фильтр по материалу"),
    sort: Optional[str] = Query("asc", description="Сортировка: asc или desc", regex="^(asc|desc)$"),
    sort_by: Optional[str] = Query("name", description="Поле для сортировки: name, type, material, price")
):
    """Расширенный поиск с множественными фильтрами и сортировкой"""
    result = products.search_products(
        name=name,
        product_type=type,
        min_price=min_price,
        max_price=max_price,
        material=material
    )
    
    # Применяем сортировку
    result = sort_products(result, sort_by, sort)
    
    return {
        "count": len(result),
        "products": result,
        "sorting": {
            "field": sort_by,
            "order": sort
        },
        "filters": {
            "name": name,
            "type": type,
            "min_price": min_price,
            "max_price": max_price,
            "material": material
        }
    }

@app.get("/products/{product_id}")
def get_product(product_id: int):
    """Получить товар по ID"""
    product = products.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product

@app.post("/products", status_code=201)
def create_product_endpoint(product: ProductCreate):
    """Создать новый товар"""
    new_product = products.create_product(
        name=product.name,
        product_type=product.type,
        material=product.material,
        price=product.price
    )
    return {
        "message": "Товар успешно создан",
        "product": new_product
    }

@app.put("/products/{product_id}")
def update_product_endpoint(product_id: int, product_update: ProductUpdate):
    """Обновить существующий товар"""
    # Получаем только не-None поля
    update_data = {k: v for k, v in product_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    
    updated = products.update_product(product_id, **update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    return {
        "message": "Товар успешно обновлен",
        "product": updated
    }

@app.delete("/products/{product_id}")
def delete_product_endpoint(product_id: int):
    """Удалить товар по ID"""
    deleted = products.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    return {"message": f"Товар с ID {product_id} успешно удален"}

@app.delete("/products")
def delete_all_products_endpoint():
    """Удалить все товары (очистить каталог)"""
    products.delete_all_products()
    return {"message": "Все товары удалены"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
