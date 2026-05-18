# Class proxy

Иногда Java-API exteraGram требует **подкласс** Java-класса (а не просто
хук метода): переопределить методы с вызовом `super()`, добавить поля и
методы, перехватить конкретную перегрузку. Для этого SDK даёт управляемый
DSL `extera_utils.classes`. catalib ре-экспортирует его целиком из
`catalib.support` (на устройстве — настоящий DSL; офлайн —
функциональные заглушки, чтобы класс-прокси импортировался и
инстанцировался в тестах).

```python
from catalib.support import (
    Base, java_subclass, joverride, joverload, jmethod,
    jfield, jconstructor, jpreconstructor, jgetmethod, jsetmethod,
    jMVELmethod, jMVELoverride, jclassbuilder, PyObj, J,
)
```

## Простейший подкласс

`Base` — обязательный базовый Python-класс; `@java_subclass` указывает
Java-класс (и при необходимости интерфейсы).

```python
from catalib.support import Base, java_subclass, jfield, joverload, find_class

ArrayList = find_class("java.util.ArrayList")


@java_subclass("java.util.ArrayList")
class CountingList(Base):
    added = jfield("int", default=0)

    @joverload("add", ["java.lang.Object"])
    def add_item(self, value):
        self.added += 1
        return super().add_item(value)


items = CountingList.new_instance()
items.add("Привет")
```

## Поля — `jfield`

`jfield(java_type, default=None, methods=None)` — поле на Java-объекте,
доступное как обычный Python-атрибут. `methods=[jgetmethod("isX"),
jsetmethod("setX")]` генерирует Java-аксессоры.

```python
counter = jfield("int", default=0)
title = jfield("java.lang.String", default="Demo")
shadow = jfield("boolean", default=False,
                methods=[jgetmethod("isShadow"), jsetmethod("setShadow")])
```

## Переопределения и добавление методов

| Декоратор | Назначение |
|-----------|------------|
| `@joverride()` / `@joverride("javaName")` | переопределить метод (имена совпадают / явное Java-имя) |
| `@joverload("name", ["arg.types"])` | переопределить конкретную перегрузку |
| `@jmethod("name", "ret.type", ["args"])` / `@jmethod()` с аннотациями | добавить новый Java-метод |
| `jMVELmethod(return_type=, arguments=, code=)` | добавить метод с телом на MVEL |
| `jMVELoverride(arguments=, code=)` | переопределить метод телом на MVEL (доступен `SUPER_<name>()`) |

## Конструкторы

| Декоратор | Когда выполняется |
|-----------|-------------------|
| `@jpreconstructor(["args"])` | до Java-конструктора; может вернуть заменённые аргументы |
| `@jconstructor(["args"])` | после создания Java-объекта |

Порядок инициализации: `@jpreconstructor` → Java-конструктор →
`__init__` → `@jconstructor` → `on_post_init`. `new_instance(*java_args,
init_args=None)` создаёт Python-peer; `instance.java` / `instance.this` —
привязанный Java-объект.

```python
@java_subclass("some.JavaClass")
class Demo(Base):
    title = jfield("java.lang.String", default="Demo")

    @jpreconstructor(["java.lang.String", "int"])
    def normalize(cls, title, count):
        return [title.strip(), max(0, count)]

    def __init__(self, title, count):
        self.python_state = {"created_with": title}

    @jconstructor(["java.lang.String", "int"])
    def init_fields(self, title, count):
        self.title = title
        self.counter = count


inst = Demo.new_instance("  Hello  ", -3)   # title="Hello", counter=0
```

## `J` — доступ к членам Java-объекта

`J(obj)` прозрачно проксирует чтение/запись полей и вызовы методов
(`JavaHelper`/`ClassHelper` — синонимы). Переключатели режимов
(`JAccessAll`, `JNotUseGetterAndSetter`, `JIgnoreResult` и др.) —
неизменяемые.

```python
from catalib.support import J

helper = J(some_java_object)
helper.title = "Обновлено"
helper.JIgnoreResult.setTitle("H").requestLayout()   # цепочка
```

## `PyObj` — перенос Python-объекта через Java

```python
from catalib.support import PyObj

payload = PyObj.create({"debug": True})
# положить в Java-поле / UItem.object; на стороне Python получить обратно
```

## Офлайн-граница

Офлайн (юнит-тесты без устройства) класс-прокси **импортируется и
инстанцируется**, `jfield` работает как атрибут со значением по
умолчанию, соблюдается порядок `jpreconstructor`→`__init__`→
`jconstructor`→`on_post_init`, `J`/`PyObj` проксируют Python-объект.
Вызовы настоящего Java-родителя (`super().javaMethod()`) и тело MVEL
исполняются только на устройстве — это документированная граница
офлайн-режима, а не недоделка. На устройстве работает настоящий DSL в
полном объёме.

## Когда использовать

- Java-API требует именно **подкласс** (не интерфейс).
- Нужны вызовы родителя через `super()`, поведение конкретной
  перегрузки, Java-поля или дополнительные методы на объекте.

Если достаточно перехватить метод — используйте
[Xposed-хуки](hooks.md#xposed-хуки). Источник истины по DSL —
официальная документация
<https://plugins.exteragram.app/docs/class-proxy>.
