import argparse
import sys
import re
# from gensim.models.keyedvectors import KeyedVectors
# from underthesea import pos_tag


chatito_ident = '    '
chatito_endline = '\n'
chatito_entity_re = r"[~|@]\[[_a-zA-Z._][_a-zA-Z0-9._]{0,30}\]"r"[\ |\t]*"r"\n"


# Declare w2v model for generating synonym words
# model = KeyedVectors.load_word2vec_format('baomoi.model.bin', binary=True)

patterns = {
    '[àáảãạăắằẵặẳâầấậẫẩ]': 'a',
    '[đ]': 'd',
    '[èéẻẽẹêềếểễệ]': 'e',
    '[ìíỉĩị]': 'i',
    '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
    '[ùúủũụưừứửữự]': 'u',
    '[ỳýỷỹỵ]': 'y'
}

def remove_tone_notation(text):
    """
    Remove Vietnamese tone notation
    text: input string to be converted
    Return: converted string which is removed ton notation
    """
    output = text
    for regex, replace in patterns.items():
        output = re.sub(regex, replace, output)
        # deal with upper case
        output = re.sub(regex.upper(), replace.upper(), output)
    return output

# temporarily commented
# def add_synonym_sentences(sentence):
#     """
#     Add synonym sentences for given sentence
#     Input: <sentence> sentence that will be used to generate synonym sentences
#     Return: List of synonym sentences
#     """
#     word_pos = pos_tag(sentence)
#     sys_sents = []
#     for word, tag in word_pos:
#         if 'V' in tag or 'N' in tag:
#             word = word.replace(" ", "_")
#             word = word.strip()
#             try:
#                 # syn_words = vi_dict[word]
#                 syn_words = model.most_similar(word)[:6]
#             except EnvironmentError:
#                 syn_words = None
#             if syn_words is not None:
#                 lst = []
#                 for syn_word, prob in syn_words:
#                     lst.append(prob)        #add to lst list, not use
#                     # splited_syn_words = split_word(syn_word, model)
#                     syn_word = syn_word.replace('_', ' ')
#                     syn_sent = sentence.replace(word, syn_word)
#                     sys_sents.append(syn_sent)
#     return sys_sents

def convert_title_case(text):
    """
    Upper case the first character of each sentence.
    text: input string to be converted
    Return: converted string which first character is uppercase
    """
    output = text.capitalize()
    return output

def augment_words(words):
    """
    Augmenting chatito data through several steps
    """


    # remove Vietnamese tone notationegs[0][0] == 0:
    tone_notation_removed_words = [remove_tone_notation(w) for w in words]

    # synonym_sentences = []
    # for w in words:
    #     synonym_sentences += add_synonym_sentences(w)

    # convert title case
    #converted_to_title_case = [convert_title_case(w) for w in words]

    # return the unique words list
    return list(set(words + tone_notation_removed_words))


# ifile_path = r"data/nlu_chatito/entities_editable/find_product.chatito"
# ofile_path = r"test.chatito"

def main():
    command = 'Augmenting chatito data using several text processing methods.'
    parser = argparse.ArgumentParser(description=command)
    parser.add_argument('infile', type=argparse.FileType('r'),
                        default=sys.stdin, help='Input chatito file')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        default=sys.stdout, help='Output chatito file')
    args = parser.parse_args()

    ifile_path = args.infile.name
    ofile_path = args.outfile.name

    with open(ifile_path, "r") as ifile, open(ofile_path, "w") as ofile:
        line = ifile.readline()
        start = False
        cnt = 1
        words = []
        while line:
            # print("Line {}: {}".format(cnt, line.strip()))
            x = re.search(chatito_entity_re, line)
            if x is not None and x.regs[0][0] == 0:
                if start:
                    # processing words
                    words = augment_words(words)
                    # print(words)
                    for w in sorted(words):
                        length = len(w)
                        if length > 0:
                            ofile.write(chatito_ident + w + chatito_endline)
                    words.clear()
                else:
                    start = True
                    words.clear()
                ofile.write(line)
            elif start:
                words.append(line.strip())
            else:
                ofile.write(line)

            line = ifile.readline()
            cnt += 1

        # processing words final time
        words = augment_words(words)
        for w in sorted(words):
            length = len(w)
            if length > 0:
                ofile.write(chatito_ident + w + chatito_endline)
        words.clear()
        ifile.close()
        ofile.close()

if __name__ == "__main__":
    main()
