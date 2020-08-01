rm -rf core.*
rm -rf ./output/snapshots/*

python3 of_cnn_train_val.py \
    --num_nodes=1 \
    --train_data_dir="home/t-zhihua/ImageRepresentation/data/ImageNetof/" \
    --train_data_part_num=40 \
    --val_data_dir="home/t-zhihua/ImageRepresentation/data/ImageNetof/" \
    --val_data_part_num=8 \
    --gpu_num_per_node=1 \
    --model_update="momentum" \
    --learning_rate=0.1 \
    --loss_print_every_n_iter=1 \
    --batch_size_per_device=32 \
    --val_batch_size_per_device=32 \
    --num_epoch=100 \
    --model="resnext50"