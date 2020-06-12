import csv
import random
from argparse import ArgumentParser
from collections import defaultdict
import os


INPUT_COLS = ['sig', 'x', 'y', 'w', 'h', 'label']
DELIMITER = '\t'

MAX_TRIPLETS_PER_OUTFIT = None  # maximum number of triplets sampled from a single outfit
SKIP_IF_POS_SAME_CATEGORY_AS_ANCHOR = True  # whether or not anchor and pos/neg must be from different categories


def read_input(input_dir):
    """
    Read raw dataset from input_dir. Assumes INPUT_COLS.
    """
    cnt = skipped_dup = 0
    data_by_sig = defaultdict(list)
    data_by_cat = defaultdict(list)
    dedup = set()
    sigs = set()
    for file in os.listdir(input_dir):
        curr_file = os.path.join(input_dir, file)
        print('Processing {}'.format(curr_file))

        with open(curr_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=INPUT_COLS, delimiter=DELIMITER)
            for row in reader:
                key = (row['sig'], row['x'], row['y'], row['w'], row['y'], row['label'])
                if key in dedup:
                    skipped_dup += 1
                    continue
                dedup.add(key)

                data_by_sig[row['sig']].append(row)
                data_by_cat[row['label']].append(row)
                sigs.add(row['sig'])

                cnt += 1
                if (cnt + skipped_dup) % 100000 == 0:
                    print('num_rows={}, num_skipped_dup={}, current_row={}'.format(cnt, skipped_dup, row))
                    print('num_sigs={}'.format(len(data_by_sig)))
                    print('num_cats={}'.format(len(data_by_cat)))

    return data_by_sig, data_by_cat


def sample_triplets(data_by_sig, data_by_cat):
    """
    Sample triplets where <anchor, pos> are from the same outfit but different categories
    and <pos, neg> are from the same category but different outfits.
    """
    triplets = set()
    cnt = 0

    for sig, items in data_by_sig.items():
        pairs_from_outfit = 0
        # shuffle items
        random.shuffle(items)
        for i in range(0, len(items) - 1):
            for j in range(i + 1, len(items)):
                if MAX_TRIPLETS_PER_OUTFIT and pairs_from_outfit >= MAX_TRIPLETS_PER_OUTFIT:
                    continue

                i_label = items[i]['label']
                j_label = items[j]['label']

                if SKIP_IF_POS_SAME_CATEGORY_AS_ANCHOR and i_label == j_label:
                    continue

                anchor = i
                pos = j

                i_x = items[anchor]['x']
                i_y = items[anchor]['y']
                i_w = items[anchor]['w']
                i_h = items[anchor]['h']
                i_label = items[anchor]['label']

                j_x = items[pos]['x']
                j_y = items[pos]['y']
                j_w = items[pos]['w']
                j_h = items[pos]['h']
                j_label = items[pos]['label']

                # sample negative from the same category as positive (but different outfit)
                neg_sample = random.choice(data_by_cat[j_label])
                while neg_sample['sig'] == sig:
                    neg_sample = random.choice(data_by_cat[j_label])

                neg_sig = neg_sample['sig']
                k_x = neg_sample['x']
                k_y = neg_sample['y']
                k_w = neg_sample['w']
                k_h = neg_sample['h']
                k_label = neg_sample['label']

                triplets.add((sig, i_x, i_y, i_w, i_h, i_label,
                              sig, j_x, j_y, j_w, j_h, j_label,
                              neg_sig, k_x, k_y, k_w, k_h, k_label))

                pairs_from_outfit += 1

                cnt += 1
                if cnt % 100000 == 0:
                    print('num_triplets={}'.format(cnt))
                    print('current_row={}'.format(list(triplets)[-1]))
    print('Done! Total number triplets : {}'.format(cnt))
    return triplets


def write_to_output(triplets, output_path):
    with open(output_path, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=DELIMITER)
        writer.writerows(triplets)
    print('row_written={} to path={}'.format(len(triplets), output_path))


def run(args):
    data_by_sig, data_by_cat = read_input(args.input_dir)
    triplets = sample_triplets(data_by_sig, data_by_cat)
    write_to_output(triplets, args.output_path)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input_dir', help='local directory of raw dataset')
    parser.add_argument('--output_path', help='path of triplet dataset output')
    args = parser.parse_args()

    run(args)
