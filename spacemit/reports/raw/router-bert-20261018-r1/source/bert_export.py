#!/usr/bin/env python3
"""为已核对的大小写敏感 WordPiece 编码器导出 F32 GGUF。"""
import argparse
import json
import logging
from pathlib import Path
import sys


def check_tokenizer(directory):
    """拒绝当前适配器不能表示的分词配置。"""
    data = json.loads((directory / 'tokenizer.json').read_text())
    normalizer = data['normalizer']
    if normalizer != {'type': 'BertNormalizer', 'clean_text': True,
                      'handle_chinese_chars': True, 'strip_accents': None, 'lowercase': False}:
        raise ValueError('unsupported BERT normalizer')
    if data['pre_tokenizer'] != {'type': 'BertPreTokenizer'}:
        raise ValueError('unsupported BERT pre-tokenizer')
    model = data['model']
    if model['type'] != 'WordPiece' or model['unk_token'] != '[UNK]' or model['continuing_subword_prefix'] != '##' or model['max_input_chars_per_word'] != 100:
        raise ValueError('unsupported WordPiece model')
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--encoder', type=Path, required=True)
    parser.add_argument('--converter', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    check_tokenizer(args.encoder)
    if args.output.exists():
        raise FileExistsError(args.output)
    sys.path.insert(0, str(args.converter))
    sys.path.insert(0, str(args.converter / 'gguf-py'))
    import gguf
    from conversion.bert import BertModel

    class CasedWordPieceBert(BertModel):
        model_arch = gguf.MODEL_ARCH.BERT

        def get_vocab_base_pre(self, tokenizer):
            return 'default'

    logging.basicConfig(level=logging.INFO)
    model = CasedWordPieceBert(args.encoder, gguf.LlamaFileType.ALL_F32, args.output)
    model.write()


if __name__ == '__main__':
    main()
