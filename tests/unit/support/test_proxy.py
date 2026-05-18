"""Тесты офлайн-контракта class-proxy (``extera_utils.classes``)."""

from __future__ import annotations

from catalib.support import proxy
from catalib.support.proxy import (
    Base,
    J,
    PyObj,
    java_subclass,
    jconstructor,
    jfield,
    jMVELmethod,
    joverride,
    jpreconstructor,
)


def test_java_subclass_keeps_class_and_records_bases() -> None:
    @java_subclass("java.util.ArrayList", "java.lang.Runnable", methods=["x"])
    class MyList(Base):
        pass

    assert MyList.__catalib_java_bases__ == (
        "java.util.ArrayList",
        "java.lang.Runnable",
    )
    assert MyList.__catalib_java_kwargs__ == {"methods": ["x"]}


def test_jfield_behaves_as_attribute_with_default() -> None:
    @java_subclass("X")
    class C(Base):
        counter = jfield("int", default=0)
        title = jfield("java.lang.String", default="Demo")

    a = C.new_instance()
    b = C.new_instance()
    assert a.counter == 0 and a.title == "Demo"
    a.counter += 5
    assert a.counter == 5
    assert b.counter == 0  # значение по экземпляру, не общее


def test_init_order_pre_init_constructor_post() -> None:
    order: list[str] = []

    @java_subclass("X")
    class Demo(Base):
        title = jfield("java.lang.String", default="")

        @jpreconstructor(["java.lang.String", "int"])
        def normalize(cls, title, count):
            order.append("pre")
            return [title.strip(), max(0, count)]

        def __init__(self, title, count):
            order.append("init")
            self.python_state = {"title": title}

        @jconstructor(["java.lang.String", "int"])
        def init_fields(self, title, count):
            order.append("ctor")
            self.title = title
            self.counter = count

        def on_post_init(self):
            order.append("post")

    inst = Demo.new_instance("  Hello  ", -3)
    assert order == ["pre", "init", "ctor", "post"]
    assert inst.title == "Hello"
    assert inst.counter == 0
    assert inst.python_state == {"title": "Hello"}
    assert inst.java is None and inst.this is None


def test_new_instance_without_custom_init_and_no_args() -> None:
    @java_subclass("java.util.ArrayList")
    class CountingList(Base):
        added = jfield("int", default=0)

    items = CountingList.new_instance()
    assert items.added == 0


def test_joverride_is_passthrough_marker() -> None:
    @java_subclass("X")
    class C(Base):
        @joverride()
        def onAttached(self):
            return "ok"

        @joverride("equals")
        def equals_(self, other):
            return True

    c = C.new_instance()
    assert c.onAttached() == "ok"
    assert c.equals_(object()) is True
    assert hasattr(C.onAttached, "__catalib_joverride__")


def test_j_wrapper_passthrough_and_modes() -> None:
    class Obj:
        def __init__(self):
            self.title = "t"

        def shout(self, s):
            return s.upper()

    o = Obj()
    h = J(o)
    assert h.title == "t"
    h.title = "x"
    assert o.title == "x"
    assert h.shout("hi") == "HI"
    # Переключатели режимов возвращают рабочую обёртку.
    assert h.JAccessAll.title == "x"
    assert h.JIgnoreResult.JNotUseGetterAndSetter.shout("a") == "A"


def test_pyobj_create_roundtrip() -> None:
    payload = PyObj.create({"debug": True})
    assert payload.value == {"debug": True}
    assert payload.get() == {"debug": True}


def test_mvel_placeholder_callable_offline() -> None:
    @java_subclass("X")
    class C(Base):
        label = jMVELmethod(return_type="java.lang.String", code="return 1;")

    c = C.new_instance()
    assert c.label() is None  # офлайн MVEL не исполняется


def test_all_exports_present() -> None:
    for name in proxy.__all__:
        assert hasattr(proxy, name)
