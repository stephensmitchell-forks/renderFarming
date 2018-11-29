import logging
from ConfigParser import NoSectionError

mlg = logging.getLogger("renderFarming.Classes")


class Camera:
    def __init__(self, name):
        self._name = name


class TokenizedString:
    # Class for handling tokenized strings
    # Assumes token format as ${section:option} and returns value
    def __init__(self, raw_string, cfg):
        self._cfg = cfg

        self._tokenDict = {"code": Token("project", "code", self._cfg),
                           "project": Token("paths", "projects_directory", self._cfg),
                           "userScripts": Token("paths", "user_scripts", self._cfg)
                           }

        self._raw_string = raw_string
        self._expanded_string = str()

        self._array = list()

        self._split_tokens(raw_string)

        self._expand()

    def __str__(self):
        return

    def _split_tokens(self, tokenized_string):
        """
        Splits string into a list, creating token objects for each token and keeping the other strings in order
        :param tokenized_string: The string with tokens in it
        :return: sets class attribute to result
        """
        token_split = tokenized_string.split('$')
        string_array = list()
        for i in token_split:
            # checks if i is a token or a normal string
            if '}' in i:
                split_array = i.replace('{', '').split('}')

                # Creates token object
                tk = self._tokenDict.get(split_array[0])

                if tk is None:
                    Token("split_array[0]", "ERROR", self._cfg)

                string_array.append(tk)
                string_array = string_array + split_array[1:]
            else:
                string_array.append(i)
        self._array = string_array

    def _expand(self):
        """
        Gets the expanded tokens and re builds the string with the expanded values substituting the tokens
        :return: sets class attribute to result
        """
        tokenized_string = str()
        for i in self._array:
            if isinstance(i, Token):
                tokenized_string = tokenized_string + i.get_value()
            else:
                tokenized_string = tokenized_string + i
        self._expanded_string = tokenized_string

    def get_expanded(self):
        return self._expanded_string


class Token:
    # Class for handling Tokens
    # Assumes token format as section:option and returns value
    def __init__(self, section, option, cfg):
        self._value = str()
        self._section = section
        self._option = option
        self._cfg = cfg

        self._expand()

    def __str__(self):
        return self._value

    def __repr__(self):
        return self.__str__()

    def _expand(self):
        """
        Looks up the section and option in the config dict and applies them to the class value.
        Warnings for missing or incorrect data will be returned
        as part of the string, rather than raising an exception here.
        :return: sets class attribute to result
        """
        try:
            self._value = self._cfg.get_config_by_section(self._section, self._option)
            return
        except NoSectionError:
            self._section = "$MISSING SECTION - {0}".format(self._section)
        except KeyError:
            self._option = "$MISSING OPTION - {0}".format(self._option)
        self._value = "{0}:{1}".format(self._section, self._option)

    def get_value(self):
        return self._value



