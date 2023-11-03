import autogen

config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": {
            # "gpt-35-turbo",
            "gpt-4-32k"
        }
    },
)
