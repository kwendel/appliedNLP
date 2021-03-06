from collections import namedtuple

from nltk import download, word_tokenize, pos_tag, WordNetLemmatizer, ngrams
from nltk.data import find
from nltk.corpus import wordnet as wn, stopwords as sw

WTReturn = namedtuple('WTReturn', ['words', 'formal_words', 'stopwords', 'pos'])
rng_WTReturn = range(0, len(WTReturn._fields))


class WordTools:
    """
    Processes sentences to extract and count words.
    """

    morphy_tag = {'NN': wn.NOUN, 'JJ': wn.ADJ,
                  'VB': wn.VERB, 'RB': wn.ADV}

    def __init__(self):

        # Download required NLTK libraries
        self.__nltk_init()

        self.lem = WordNetLemmatizer()
        self.stopwords = sw.words('english')

    def preprocess(self, sentence):

        # Convert unrecognized unicode apostrophes back to regular ones
        sentence = sentence.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')

        # Remove @ and # symbols (which are treated as single words by the NLTK tokenizer)
        sentence = sentence.replace("@", "").replace("#", "")

        return sentence

    def process(self, sentence, max_words=None, processed=False, remove_digits=False, remove_stopwords=False):
        """
        Preprocess string, tokenize, get PoS tags, lookup lemmatized words in WordNet and return:
            - All words (tokens) in the sentence
            - All formal words in the sentence (lemmas found in WordNet)
            - Part-of-Speech tags.

        Optionally filters stopwords and/or cardinal digits.
        """

        if not processed and not isinstance(sentence, str):
            raise ValueError("Word features can only be extracted from a single string.")

        if not processed:
            sentence = self.preprocess(sentence)

        # Convert string to tokens (and discard empty tokens)
        # Optionally cap number of words to deal with outliers
        tokens = list(filter(None, word_tokenize(sentence)))[:max_words]

        # Lowercase tokens except for NE (and remove empty tokens with 'if token', PoS cant handle this)
        # tokens = [WordTools.convert_ner_case(token) for token in tokens if token[0]]
        # TODO: removed, NER tagging outside the Stanford NLP pipeline takes too long / much duplicate effort

        # Get PoS tags
        # See: https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
        # Note: this is not very accurate for post titles with title case (You Will Never Believe)
        pos_raw = pos_tag(tokens)

        # Remove punctuation
        pos = self.__filter_tags(pos_raw, {'.', ':', ',', "''", '$', "``", "(", ")"})

        # Optionally remove digits (PoS tag 'CD' - Cardinal Digit)
        if remove_digits:
            pos = self.__filter_tags(pos, {'CD'})

        # Split words and stop words, optionally remove from original word list
        pos, stopwords = self.__split_stopwords(pos, remove_stopwords)

        # Separate the words from the PoS-tag tuples
        all_words, all_tags = self.__split_words_tags(pos)

        # Generate 2- and 3-grams (words)
        # word_2gram, word_3gram = self.__get_ngrams(all_words, 2, 3)
        # TODO: removed, future work

        # Generate 2- and 3-grams (pos)
        # pos_2gram, pos_3gram = self.__get_ngrams(all_tags, 2, 3)
        # TODO: removed, re-enable once PoS tagging is more accurate

        # Map PoS tags to WordNet tags, lemmatize and find lemmas in WordNet
        wn_pos = [self.__penn_to_wn(x) for x in pos]
        lemmas = [self.lem.lemmatize(word, tag) for word, tag in wn_pos]
        formal_words = [lemma for lemma in lemmas if wn.synsets(lemma)]

        return WTReturn(all_words, formal_words, stopwords, pos)

    def process_list(self, sentence_list, max_words=None, processed=False, remove_digits=False, remove_stopwords=False):

        results = map(lambda x: self.process(x, max_words, processed, remove_digits, remove_stopwords), sentence_list)
        merged = tuple([i[x] for i in results] for x in rng_WTReturn)
        return WTReturn(*merged)

    def __split_words_tags(self, pos_tuple):
        words = []
        tags = []

        for tup in pos_tuple:
            words.append(tup[0])
            tags.append(tup[1])

        return words, tags

    def __pos_tags_to_wordnet(self, word_tag):
        """
        Converts default NLTK PoS tags to WordNet-compatible tags.
        Inspired by: https://stackoverflow.com/a/35465203
        """

        try:
            tag = self.morphy_tag[word_tag[1][:2]]
        except:
            tag = wn.NOUN

        return word_tag[0], tag

    def __penn_to_wn(self, tag):
        """
        Convert between a Penn Treebank tag to a simplified Wordnet tag
        Source: https://nlpforhackers.io/wordnet-sentence-similarity/
        """

        t = tag[1]

        if t.startswith('N'):
            nt = 'n'

        elif t.startswith('V'):
            nt = 'v'

        elif t.startswith('J'):
            nt = 'a'

        elif t.startswith('R'):
            nt = 'r'

        else:
            nt = 'n'

        return tag[0], nt

    def __split_stopwords(self, words, remove=False):
        """
        Splits stop words from the provided word list.
        Optionally removes the words from the original list.
        """

        stopwords = []
        filter_words = []

        for pos_tuple in words:

            if pos_tuple[0] in self.stopwords:
                stopwords.append(pos_tuple)
            elif not remove:
                filter_words.append(pos_tuple)

        if remove:
            return filter_words, stopwords
        else:
            return words, stopwords

    def __filter_tags(self, list_of_tuples, tags: set) -> list:
        """Removes words from list of word/tag tuples if tag matches function argument."""

        return [word_tag for word_tag in list_of_tuples if word_tag[1] not in tags]

    def __get_ngrams(self, words, n1, n2):

        n1gram = list(ngrams(words, n1))
        n2gram = list(ngrams(words, n2))

        return n1gram, n2gram

    def __nltk_init(self):
        """Download and install NLTK resources if not found on the system."""

        try:
            find('corpora/wordnet.zip')
        except LookupError:
            download('wordnet')

        try:
            find('tokenizers/punkt/english.pickle')
        except LookupError:
            download('punkt')

        try:
            find('taggers/averaged_perceptron_tagger.zip')
        except LookupError:
            download('averaged_perceptron_tagger')

        try:
            find('corpora/stopwords.zip')
        except LookupError:
            download('stopwords')
        try:
            find('sentiment/vader_lexicon.zip')
        except LookupError:
            download('vader_lexicon')

    @staticmethod
    def convert_ner_case(tagged):
        return tagged[0].lower() if tagged[1] == 'O' else tagged[0].title()
