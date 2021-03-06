rm -rf core.*
rm -rf ./output/snapshots/*

python3 of_cnn_train_val.py \
    --num_nodes=1 \
    --train_data_dir="/vqa_dataset_southeastasia/ImageRepresentation/data/ImageNetof/ImageNetof/" \
    --train_data_part_num=40 \
    --val_data_dir="/vqa_dataset_southeastasia/ImageRepresentation/data/ImageNetof/ImageNetof/" \
    --val_data_part_num=8 \
    --gpu_num_per_node=8 \
    --loss_print_every_n_iter=100 \
    --batch_size_per_device=32 \
    --val_batch_size_per_device=32 \
    --num_epoch=100 \
    --model="resnext50"