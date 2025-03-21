import random

__left_name = [
    "cute",
    "fluffy",
    "small",
    "dangerous",
    "dead",
    "evil",
    "friendly",
    "mysterious",
    "fast"
]

__right_name = [
    "Alicorn",
    "Banshee",
    "Basilisk",
    "Bigfoot",
    "Bogeyman",
    "Bogle",
    "Centaur",
    "Cerberus",
    "Charybdis",
    "Chimera",
    "Cyclops",
    "Demon",
    "Doppelganger",
    "Dragon",
    "Dwarf",
    "Echidna",
    "Elf",
    "Fairy",
    "Firefox",
    "Ghosts",
    "Gnome",
    "Goblin",
    "Golem",
    "Gorgon",
    "Griffin",
    "GrimReaper",
    "Hobgoblin",
    "Hydra",
    "Imp",
    "Ladon",
    "Leprechauns",
    "Manticore",
    "Medusa",
    "Mermaids",
    "Minotaur",
    "Mothman",
    "Mutants",
    "New",
    "Nymph",
    "Ogre",
    "Orthros",
    "Pegasus",
    "Phoenix",
    "Pixie",
    "Sasquatch",
    "Satyr",
    "Scylla",
    "SeaMonsters",
    "SeaGoat",
    "Shade",
    "Shapeshifters",
    "Sirens",
    "Sphinx",
    "Sprite",
    "Sylph",
    "Thunderbird",
    "Typhon",
    "Unicorn",
    "Valkyries",
    "Vampire",
    "Wendigo",
    "Werewolf",
    "Wraith",
    "Zombie"
]


def generate_name():
    return str(random.choice(__left_name)) + "_" + str(random.choice(__right_name))
