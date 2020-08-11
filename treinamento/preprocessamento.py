
import os
import re
import magic
import librosa
from treinamento import audio
import numpy as np
#from keras.utils import np_utils
from sklearn.feature_extraction.text import CountVectorizer

'''
REFERÊNCIAS: 

https://panda.ime.usp.br/pensepy/static/pensepy/10-Arquivos/files.html
https://github.com/aravindpai/Speech-Recognition/blob/master/Speech%20Recognition.ipynb
https://medium.com/@patrickbfuller/librosa-a-python-audio-libary-60014eeaccfb
https://keras.io/examples/audio/speaker_recognition_using_cnn/
https://blogs.rstudio.com/ai/posts/2018-06-06-simple-audio-classification-keras/
https://github.com/manashmandal/DeadSimpleSpeechRecognizer/blob/master/preprocess.py
https://medium.com/manash-en-blog/building-a-dead-simple-word-recognition-engine-using-convnet-in-keras-25e72c19c12b
https://en.wikipedia.org/wiki/Mel-frequency_cepstrum
https://www.kaggle.com/ilyamich/mfcc-implementation-and-tutorial
https://haythamfayek.com/2016/04/21/speech-processing-for-machine-learning.html

Exploiting spectro-temporal locality in deep learning based acoustic event detection
https://link.springer.com/article/10.1186/s13636-015-0069-2

https://python-speech-features.readthedocs.io/en/latest/
https://speechpy.readthedocs.io/_/downloads/en/stable/pdf/

https://librosa.org/doc/latest/feature.html
https://librosa.org/doc/latest/generated/librosa.feature.melspectrogram.html
https://stackoverflow.com/questions/60492462/mfcc-python-completely-different-result-from-librosa-vs-python-speech-features
https://github.com/astorfi/speechpy/blob/master/speechpy/feature.py
https://datascience.stackexchange.com/questions/27634/how-to-convert-a-mel-spectrogram-to-log-scaled-mel-spectrogram



'''
class TreinamentoCNN(object):


    def obterDicionarioTreinamento(self):

        caminho_arquivos_treinamento = '../../corpus'
        treinamento_dicionario = {}

        for (root, dirs, arquivos) in os.walk(caminho_arquivos_treinamento):
            for arquivo in arquivos:
                if '.data' in arquivo and '.data.orig' not in arquivo:

                    arquivo_utts = os.path.join(root, arquivo)

                    '''
                    https://stackoverflow.com/questions/436220/how-to-determine-the-encoding-of-text
                    UnicodeDecodeError: 'utf-8' codec can't decode byte 0x92 in position 16: invalid start byte
                    Tentando evitar UnicodeDecodeError
                    '''
                    blob = open(arquivo_utts, 'rb').read()
                    m = magic.Magic(mime_encoding=True)
                    encoding = m.from_buffer(blob)

                    # https://stackoverflow.com/questions/16465399/need-the-path-for-particular-files-using-os-walk
                    ref_arquivo = open(arquivo_utts, "r", encoding=encoding)
                    padrao_regex = '(\d\d\d_yoruba_.*_headset_)(\d\d\d)(\d)?'


                    try:

                       for linha in ref_arquivo:

                            arquivo_audio = re.search(padrao_regex, linha).group()
                            transcricao = re.search('".*"', linha).group().replace('"', '')
                            treinamento_dicionario[arquivo_audio] = transcricao



                    except UnicodeError as e:
                        pass

                    ref_arquivo.close()

        return treinamento_dicionario

    listaAudiosTreinamento = []


    def carregarAudiosTreinamento(self, nome_audio, label_encoded):

        caminho_arquivos_treinamento = '../../corpus'
        dimensao_maxima = 10

        for (root, dirs, arquivos) in os.walk(caminho_arquivos_treinamento):
            for arquivo in arquivos:

                if nome_audio+'.wav' in arquivo:

                    sinal_audio, sample_rate = librosa.load(os.path.join(root, nome_audio+'.wav'), sr = 16000)

                    espectograma = librosa.feature.melspectrogram(y=sinal_audio, sr=sample_rate)

                    '''
                                        https://en.wikipedia.org/wiki/Mel-frequency_cepstrum

                                        The experimental results in Section V show
                                        a consistent improvement in overall system performance by
                                        using the log-energy feature. There has been some question
                                        as to whether this improvement holds in larger-scale ASR
                                        tasks [40]. Nevertheless, these experiments at least show that
                                        nothing in principle prevents frequency-independent features
                                        such as log-energy from being accommodated within a CNN
                                        architecture when they stand to improve performance. (p.1539)   
                                        https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/CNN_ASLPTrans2-14.pdf?irgwc=1&OCID=AID2000142_aff_7806_1246483&tduid=%28ir__3n1mp6niookftmjtkk0sohzjxm2xilegkfdgcd0u00%29%287806%29%281246483%29%28%283283fab34b8e9cb7166fb504c2f02716%29%2881561%29%28686431%29%28at106140_a107739_m12_p12460_cBR%29%28%29%29%283283fab34b8e9cb7166fb504c2f02716%29&irclickid=_3n1mp6niookftmjtkk0sohzjxm2xilegkfdgcd0u00 

                                        https://stackoverflow.com/questions/60492462/mfcc-python-completely-different-result-from-librosa-vs-python-speech-features                    
                                        
                                        https://pytorch.org/audio/transforms.html#spectrogram
                                        
                                        https://pytorch.org/tutorials/beginner/audio_preprocessing_tutorial.html

                                        http://man.hubwiz.com/docset/LibROSA.docset/Contents/Resources/Documents/_modules/librosa/core/spectrum.html#power_to_db


                                        def power_to_db(S, ref=1.0, amin=1e-10, top_db=80.0):
                                        Convert a power spectrogram (amplitude squared) to decibel (dB) units

                                        This computes the scaling ``10 * log10(S / ref)`` in a numerically
                                        stable way.
                                        
                                        TECHNIQUES FOR FEATURE EXTRACTION IN SPEECH
                                        RECOGNITION SYSTEM : A COMPARATIVE STUDY 
                                        https://arxiv.org/pdf/1305.1145.pdf
                                        
                                        https://en.wikipedia.org/wiki/Mel-frequency_cepstrum
                                        https://en.wikipedia.org/wiki/Spectral_density#Power_spectral_density
                                        
                                        Não estou usando DCT, mas log-energy 
                                        https://en.wikipedia.org/wiki/Discrete_cosine_transform
                                        
                                        https://docs.python.org/2/tutorial/datastructures.html#dictionaries
                                        https://developer.rhino3d.com/guides/rhinopython/primer-101/6-tuples-lists-dictionaries/

                    '''

                    log_energy_espectograma = librosa.power_to_db(espectograma)

                    '''
                    Garante que os vetores mfcc tenham o mesmo tamanho fixo através de um padding de 0 
                    em volta do vetor mfcc, caso ele tenha dimensão menor do que um valor máximo pré-fixado

                    https://www.kaggle.com/ilyamich/mfcc-implementation-and-tutorial

                    How to normalize MFCCs
                    https://www.kaggle.com/c/freesound-audio-tagging/discussion/54082

                    '''

                    if (dimensao_maxima > log_energy_espectograma.shape[1]):

                        padding = dimensao_maxima - log_energy_espectograma.shape[1]
                        mel_frequency_cepstrum_coefficients = np.pad(log_energy_espectograma, pad_width=((0, 0), (0, padding)), mode='constant')

                    # Else cutoff the remaining parts
                    else:
                        mel_frequency_cepstrum_coefficients = log_energy_espectograma[:, : dimensao_maxima]

                    audioObj = audio.Audio(log_energy_espectograma, label_encoded)
                    self.listaAudiosTreinamento.append(audioObj)


    def converterTranscricaoCategoricalDecoder(self, dicionario_treinamento_raw):
        '''

        from keras.utils import to_categorical

        https://keras.io/examples/
        https://keras.io/examples/audio/speaker_recognition_using_cnn/
        https://github.com/attardi/CNN_sentence
        https://github.com/attardi/CNN_sentence/blob/master/process_data.py
        https://scikit-learn.org/stable/modules/multiclass.html
        https://medium.com/@maobedkova/acoustic-word-embeddings-fc3f1a8f0519
        https://medium.com/@oyewusiwuraola/yor%C3%B9b%C3%A1-word-vector-representation-with-fasttext-fe905bf558ea
        https://github.com/Niger-Volta-LTI

        https://www.youtube.com/channel/UCoEHw2cfZ0YJNQUKeWxLuWg

        '''

        # labels_encoded[0].vocabulary_   devolve o índice de cada palavra
        labels_encoded = self.vetorizador(dicionario_treinamento_raw.values())
        #print(labels_encoded[0].inverse_transform(labels_encoded[1]))

        '''
        Testando voltar para a transcrição original após vetorização
        Preciso garantir aqui que as transcrições vetorizadas combinem exatamente com os audios

        '''

        #transcricao_convertida_teste = labels_encoded[0].inverse_transform(list(dicionario_labels_encoded.values())[0])
        #print(transcricao_convertida_teste)

        #return dicionario_labels_encoded


    def vetorizador(self, listaSentencas):

        '''

        https://www.oreilly.com/library/view/applied-text-analysis/9781491963036/ch04.html
        https://developers.google.com/machine-learning/guides/text-classification/step-3?hl=pl


        https://developers.google.com/machine-learning/guides/text-classification/step-4?hl=pl

        DECISÕES:

        1. Precisarei usar sequence models e word embedding
        2. Usar um word embedding já treinado ou treinar com os dados que possuo ?
        3. Usarei AWE (Acoustic Word Embedding) ou somente TWE (Textual Word Embedding) ?

        LINKS ÚTEIS:
        https://medium.com/@maobedkova/acoustic-word-embeddings-fc3f1a8f0519
        https://medium.com/@oyewusiwuraola/yor%C3%B9b%C3%A1-word-vector-representation-with-fasttext-fe905bf558ea
        https://github.com/Niger-Volta-LTI


        https://fasttext.cc/docs/en/pretrained-vectors.html
        P. Bojanowski*, E. Grave*, A. Joulin, T. Mikolov, Enriching Word Vectors with Subword Information

        @article{bojanowski2017enriching,
        title={Enriching Word Vectors with Subword Information},
        author={Bojanowski, Piotr and Grave, Edouard and Joulin, Armand and Mikolov, Tomas},
        journal={Transactions of the Association for Computational Linguistics},
        volume={5},
        year={2017},
        issn={2307-387X},
        pages={135--146}
        }

        wget https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.yo.zip
        Length: (2,1 GB)

        '''

        vetorizador = CountVectorizer()
        vetorizador.fit(listaSentencas)
        print(vetorizador.vocabulary_)
        vetor_labels = vetorizador.transform(listaSentencas)
        print(vetor_labels.shape)
        print(type(vetor_labels))
        print(vetor_labels.toarray())
        print(vetorizador.inverse_transform(vetor_labels))

        return vetorizador, vetor_labels




from joblib import Parallel, delayed
import time

if __name__ == '__main__':

    inicio = time.clock()

    treinamento = TreinamentoCNN()
    dicionario_treinamento_raw = treinamento.obterDicionarioTreinamento()

    dicionario_treinamento = treinamento.converterTranscricaoCategoricalDecoder(dicionario_treinamento_raw)


    '''
    parallel = Parallel(backend="threading", verbose=1)
    parallel(delayed(treinamento.carregarAudiosTreinamento)(key, dicionario_treinamento[key]) for key in dicionario_treinamento)

    tempo_processamento = time.clock() - inicio

    print(treinamento.listaAudiosTreinamento[1])
    print('Tempo de processamento {}'.format(tempo_processamento))
    '''