
import os
import re
import magic
import librosa
from scipy.io import wavfile
from scipy.signal import stft
from treinamento import audio
import numpy as np
#from keras.utils import np_utils
from sklearn.feature_extraction.text import CountVectorizer
from treinamento import audio
import time
#import psutil
from util.paralelizacao import Paralelizacao
from util.sequencial import Sequencial

import csv


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
class PreProcessamento(object):


    listaGlobalAudios = []
    vocabulario = []
    configuracao_paralelismo = {}
    dimensao_maxima_vetor_audios = 180

    def __init__(self, numJobs=4, verbose=5, backend='multiprocessing', executarEmParalelo=True):

        '''
        https://stackabuse.com/parallel-processing-in-python/
        https://www.machinelearningplus.com/python/parallel-processing-python/#:~:text=In%20python%2C%20the%20multiprocessing%20module,in%20completely%20separate%20memory%20locations.


        https://psutil.readthedocs.io/en/release-2.2.1/
        '''

        '''
        PARÂMETROS DE PARALELIZAÇÃO
        https://joblib.readthedocs.io/en/latest/generated/joblib.Parallel.html

        n_jobs = 4   # máximo número de cpus = psutil.cpu_count() 

        using ‘n_jobs=1’ enables to turn off parallel computing for debugging without changing the codepath

        backend = "multiprocessing"    
        backend = "threading"

        “loky” used by default, can induce some communication and memory overhead when exchanging input and output data with the worker Python processes.
    “multiprocessing” previous process-based backend based on multiprocessing.Pool. Less robust than loky.
    “threading” is a very low-overhead backend but it suffers from the Python Global Interpreter Lock if the called function relies a lot on Python objects. “threading” is mostly useful when the execution bottleneck is a compiled extension that explicitly releases the GIL (for instance a Cython loop wrapped in a “with nogil” block or an expensive call to a library such as NumPy).
    finally, you can register backends by calling register_parallel_backend. This will allow you to implement a backend of your liking.

        https://scikit-learn.org/stable/modules/generated/sklearn.utils.parallel_backend.html
        https://stackoverflow.com/questions/59136430/how-does-scikit-learn-handle-multiple-n-jobs-arguments

        TESTAR DIFERENTES PARÂMETROS DE PARALELIZAÇÃO E VER O EFEITO EM TEMPO E MEMÓRIA
        '''
        if executarEmParalelo == False:
            numJobs=1
            backend='SequencialBackend'

        configuracao_paralelizacao = {}
        # using ‘n_jobs=1’ enables to turn off parallel computing for debugging without changing the codepath
        configuracao_paralelizacao['n_jobs'] = numJobs
        configuracao_paralelizacao['verbose'] = verbose
        configuracao_paralelizacao['backend'] = backend

        self.executarEmParalelo = executarEmParalelo
        self.configuracao_paralelismo = configuracao_paralelizacao


    def carregarListaAudiosNomesArquivosTranscricoes(self):

        print('Iniciando montagem da lista com nomes dos arquivos de áudio e transcrições')

        caminho_arquivos_treinamento = '../../corpus'

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

                            nome_arquivo_audio = re.search(padrao_regex, linha).group()
                            transcricao = re.search('".*"', linha).group().replace('"', '')
                            audioObj = audio.Audio(nome_arquivo_audio, None, transcricao, None, None)
                            self.listaGlobalAudios.append(audioObj)
                            self.vocabulario.append(transcricao)


                    except UnicodeError as e:
                        pass

                    ref_arquivo.close()


    path_arquivo_caminhos_audios = '/home/usuario/mestrado/yorubaSpeechRecognition_RECOVERY/arquivo_caminhos_audios.txt'

    def criarArquivoComCaminhosParaArquivosAudio(self):

        self.carregarListaAudiosNomesArquivosTranscricoes()

        print('Iniciando atualização de caminhos para arquivos de áudio')
        caminho_arquivos_treinamento = '../../corpus'

        file = open(self.path_arquivo_caminhos_audios, 'a')

        for audio in self.listaGlobalAudios:
            for (root, dirs, arquivos) in os.walk(caminho_arquivos_treinamento):
                for arquivo in arquivos:
                    if audio.nome_arquivo + '.wav' in arquivo:
                        caminho_audio = os.path.join(root, audio.nome_arquivo + '.wav' + '__TRANSCRICAO__'+audio.transcricao+'__TRANSCRICAO__')
                        file.write(caminho_audio)
                        file.write('\n')
        
        file.close()

    def carregarListaAudios_(self, nomeArquivo):

        padrao_regex = '(.*)(__TRANSCRICAO__(.*)__TRANSCRICAO__)'
        transcricao = re.search(padrao_regex, nomeArquivo).group(3)
        nomeArquivo = re.search(padrao_regex, nomeArquivo).group(1)
        audioObj = audio.Audio(None, nomeArquivo.replace('\n', '') + '.wav', transcricao, None, None)
        self.listaGlobalAudios.append(audioObj)


    def carregarListaGlobalAudiosTreinamento(self):

        print('Iniciando conversão dos audios em espectogramas e log_energy')

        listaArquivosWave = [line for line in open(self.path_arquivo_caminhos_audios, 'r').readlines()]


        if self.executarEmParalelo:
            Paralelizacao().executarMetodoParalelo(self.carregarListaAudios_,
                                                   listaArquivosWave)
        else:
            Sequencial().executarMetodoEmSequencia(self.carregarListaAudios_,
                                                   listaArquivosWave)



        if self.executarEmParalelo:
            Paralelizacao().executarMetodoParalelo(self.processarWaveFilesComSciPy,
                                                   self.listaGlobalAudios)
        else:
            Sequencial().executarMetodoEmSequencia(self.processarWaveFilesComSciPy,
                                                   self.listaGlobalAudios)


        '''

        if self.executarEmParalelo:
            Paralelizacao().executarMetodoParalelo(self.extrairLogEnergyMelSpectogram,
                                                   self.listaGlobalAudios)
        else:
            Sequencial().executarMetodoEmSequencia(self.extrairLogEnergyMelSpectogram,
                                                   self.listaGlobalAudios)
        
        '''


    def extrairLogEnergyMelSpectogram(self, audio):

        dimensao_maxima = self.dimensao_maxima_vetor_audios
        sinal_audio, sample_rate = librosa.load(audio.caminho_arquivo, sr=16000)
        print('SINAL DE ÁUDIO: '+ str(len(sinal_audio)))
        #https://github.com/aravindpai/Speech-Recognition/blob/master/Speech%20Recognition.ipynb
        #samples = librosa.resample(sinal_audio, sample_rate, 29980)
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
        
        Melody Accompainment Separation - Examples
        https://linux.ime.usp.br/~shayenne/mac0499/results/Examples
        
        ***Nos arquivos da bíblia em Yorubá talvez seja necessário retirar melodias de fundo 


        https://www.kdnuggets.com/2020/02/audio-data-analysis-deep-learning-python-part-1.html

        https://github.com/rolczynski/Automatic-Speech-Recognition/tree/master/automatic_speech_recognition/features
        '''

        if (dimensao_maxima > log_energy_espectograma.shape[1]):

            padding = dimensao_maxima - log_energy_espectograma.shape[1]
            log_energy_espectograma = np.pad(log_energy_espectograma, pad_width=((0, 0), (0, padding)),
                                                         mode='constant')

        # Else cutoff the remaining parts
        else:
            log_energy_espectograma = log_energy_espectograma[:, : dimensao_maxima]

        audio.log_energy = log_energy_espectograma
        self.gravarDados(audio)


    def processarWaveFilesComSciPy(self, audio, threshold_freq=5500):

        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.wavfile.read.html
        # https://github.com/dawidkopczyk/speech_recognition

        _, wav = wavfile.read(audio.caminho_arquivo)
        # Normalize
        wav = wav.astype(np.float32) / np.iinfo(np.int16).max

        sample_rate = 16000

        # If longer then randomly truncate
        if len(wav) > sample_rate:
            i = np.random.randint(0, len(wav) - sample_rate)
            wav = wav[i:(i + sample_rate)]

        elif len(wav) < sample_rate:
            rem_len = sample_rate - len(wav)
            silence_part = np.random.randint(-100, 100, 16000).astype(np.float32) / np.iinfo(np.int16).max
            j = np.random.randint(0, rem_len)
            silence_part_left = silence_part[0:j]
            silence_part_right = silence_part[j:rem_len]
            wav = np.concatenate([silence_part_left, wav, silence_part_right])
        # Create spectrogram using discrete FFT (change basis to frequencies)
        freqs, times, espectograma = stft(wav, sample_rate, nperseg=400, noverlap=240, nfft=512, padded=False, boundary=None)
        # Cut high frequencies
        if threshold_freq is not None:
            espectograma = espectograma[freqs <= threshold_freq, :]
            freqs = freqs[freqs <= threshold_freq]

        # Log spectrogram
        log_energy_espectograma = np.log(np.abs(espectograma) + 1e-10)

        #log_energy = np.expand_dims(log_energy_espectograma, axis=2)
        audio.log_energy = log_energy_espectograma
        self.gravarDados(audio)




    vetorizador = CountVectorizer()


    def converterTranscricaoCategoricalDecoder(self):
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
        #labels_encoded = self.vetorizador(dicionario_treinamento_raw.values())
        #print(labels_encoded[0].inverse_transform(labels_encoded[1]))

        inicio_vetorizacao = time.clock()

        self.vetorizador.fit(self.vocabulario)

        if self.executarEmParalelo:
            Paralelizacao().executarMetodoParalelo(self.vetorizar_transcricao, self.listaGlobalAudios)
        else:
            Sequencial().executarMetodoEmSequencia(self.vetorizar_transcricao, self.listaGlobalAudios)

        processamento_vetorizacao = time.clock() - inicio_vetorizacao
        print('Tempo de processamento da vetorizacao {}'.format(processamento_vetorizacao))

        '''
        Testando voltar para a transcrição original após vetorização
        Preciso garantir aqui que as transcrições vetorizadas combinem exatamente com os audios
        '''
        for audio in self.listaGlobalAudios:
            transcricao_convertida_teste = self.vetorizador.inverse_transform(audio.label_encoded)
            print(transcricao_convertida_teste)
            break


    def vetorizar_transcricao(self, audio):
        vetor_encoded = self.vetorizador.transform([audio.transcricao])
        audio.label_encoded = vetor_encoded


    def vetorizador_sequence(self, vetorizador, listaSentencas):

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
        pass



    def obterDados(self):

        #self.criarArquivoComCaminhosParaArquivosAudio()
        #self.converterTranscricaoCategoricalDecoder()
        #self.vocabulario = [] # Neste ponto não preciso mais da lista de vocabulários
        self.carregarListaGlobalAudiosTreinamento()

        '''
        !!! StackOverflow !!!
        parallel = Parallel(backend="threading", verbose=1)
        parallel(delayed(treinamento.carregarListaGlobalAudiosTreinamento)(key, treinamento.dicionario_treinamento_encoded[key]) for key in treinamento.dicionario_treinamento_encoded)
        '''

        return self.listaGlobalAudios


    para_gravar_CSV = []


    def gravarDados(self, audio):

        '''
        https://www.kdnuggets.com/2020/02/audio-data-analysis-deep-learning-python-part-1.html
        
        :param audio: 
        :return: 

        #Preciso decidir se farei padding ou não
        for i in range (1, self.dimensao_maxima_vetor_audios):
            self.para_gravar_CSV.append(f'{np.mean(audio.log_energy[:, i])}')

        self.para_gravar_CSV.append(f'{audio.transcricao}')

        '''

        path = '/home/usuario/mestrado/yorubaSpeechRecognition_RECOVERY/dadosVetorizados/audios_vetorizados'
        file = open(os.path.join(path, f'{audio.transcricao}.csv'), 'w')
        np.savetxt(file, audio.log_energy, delimiter=",")
        file.close()





if __name__ == '__main__':

    #backend = ["loky", "multiprocessing", "threading"]
    #PreProcessamento(numJobs=1, backend=backend[0], verbose=5)
    #PreProcessamento().carregarListaGlobalAudiosTreinamento_(paralelo=False, monitorarExecucao=False)

    PreProcessamento().obterDados()
