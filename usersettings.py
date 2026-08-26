import os
import formula
import json
import ast
import sys
import traceback


class UserSettingsError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code

    def __str__(self):
        return f"{self.args[0]} (code: {self.code})"

def safe_raise(exception):
    try:
        raise exception
    except Exception:
        traceback.print_exc()

class Dict(dict):
    def __init__(self, name, data=None, on_set=None):
        super().__init__()
        self.name = name
        for k in (data or {}):
            super().__setitem__(k, data[k])
        self.on_set = on_set

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self.on_set is not None:
            self.on_set(self.name, key)

    def __delitem__(self, key):
        super().__delitem__(key)
        if self.on_set is not None:
            self.on_set(self.name, key)

class UserSettings:
    def __init__(self):
        self.__dict__["__filename"] = "usersettings.9csave"
        self.__dict__["autosave"] = True

        self.__dict__["theme"] = "Dark"
        self.__dict__["formula"] = formula.BASE_FORMULA
        self.__dict__["binders"] = Dict("binders", on_set=self.check_saving)

        self.__dict__["__write_array"] = [("theme", "str"), ("formula", "str"), ("binders", "dict")]

    def __getattr__(self, item):
        return self.__dict__.get(item.replace("_UserSettings", ""), None)

    def __setattr__(self, key, value):
        if "__" in key:
            print(f"[USERSETTINGS] no( go fuck yourself)t assigning \"{key}\", fuck you")
            return
        if key not in self.__dict__:
            print(f"[USERSETTINGS] cannot create a new property \"{key}\" (restricted)")
            return
        self.__dict__[key] = value
        self.check_saving(key)

    def __setitem__(self, key, value):
        if "__" in key:
            print(f"[USERSETTINGS] no( go fuck yourself)t assigning \"{key}\", fuck you")
            return
        if key not in self.__dict__:
            print(f"[USERSETTINGS] cannot create a new property \"{key}\" (restricted)")
            return

    def check_saving(self, name, *_):
        if self.autosave and (name in [x[0] for x in self.__write_array]):
            self.save()

    def load(self):
        if not self.exists():
            self.save()
        try:
            with open(self.get_full_filepath(), mode="r", encoding="utf-8") as file:
                for line in file.readlines():
                    split = line.split("=")
                    arg, dat, val = split[0], split[1], "".join(split[2:]).strip()
                    if dat == "dict":
                        try:
                            val = json.loads(val)
                        except json.JSONDecodeError:
                            val = ast.literal_eval(val)
                        val = Dict(arg, data=val, on_set=self.check_saving)
                    self.__dict__[arg] = val
                file.close()
        except Exception as e:
            safe_raise(UserSettingsError(f"failed to load data: {e}", -1))
            self.save()

    def save(self):
        with open(self.get_full_filepath(), mode="w", encoding="utf-8") as file:
            file.write("\n".join([f"{x[0]}={x[1]}={self.__dict__[x[0]]}" for x in self.__write_array]))
            file.close()

    def get_full_filepath(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), self.__filename)

    def exists(self):
        return os.path.exists(self.get_full_filepath())
