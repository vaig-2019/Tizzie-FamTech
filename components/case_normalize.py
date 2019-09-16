from rasa.nlu.components import Component

class CaseNormalize(Component):
    """A custom case normalizer"""

    name = "case_normalize"
    provides = ["tokens"]
    requires = ["tokens"]
    defaults = {}
    language_list = ["vi"]

    def process(self, message, **kwargs):
        """Retrieve the tokens of the new message, pass it to the classifier
            and append prediction results to the message class."""

        tokens = [t.text.lower() for t in message.get("tokens")]

        message.set("tokens", [tokens], add_to_output=True)

    @classmethod
    def load(cls,
             model_dir=None,
             model_metadata=None,
             cached_component=None,
             **kwargs):

        meta = model_metadata.for_component(cls.name)
        return cls(meta)
