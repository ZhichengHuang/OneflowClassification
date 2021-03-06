from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import math
import oneflow
import ofrecord_util
import config as configs
from util import Snapshot, Summary, InitNodes, Metric
from job_function_util import get_train_config, get_val_config
import resnext_model

parser = configs.get_parser()
args = parser.parse_args()
configs.print_args(args)

total_device_num = args.num_nodes * args.gpu_num_per_node
train_batch_size = total_device_num * args.batch_size_per_device
val_batch_size = total_device_num * args.val_batch_size_per_device
(C, H, W) = args.image_shape
epoch_size = math.ceil(args.num_examples / train_batch_size)
num_val_steps = int(args.num_val_examples / val_batch_size)

model_dict={
    "resnext50": resnext_model.resnext50,
}

oneflow.config.gpu_device_num(args.gpu_num_per_node)
oneflow.config.enable_debug_mode(True)

def label_smoothing(labels, classes, eta, dtype):
    assert classes > 0
    assert eta >= 0.0 and eta < 1.0

    return oneflow.one_hot(labels, depth=classes, dtype=dtype,
                        on_value=1 - eta + eta / classes, off_value=eta/classes)

@oneflow.global_function("train", get_train_config(args))
def TrainNet():
    if args.train_data_dir:
        assert os.path.exists(args.train_data_dir)
        print("Loading data from {}".format(args.train_data_dir))
        (labels, images) = ofrecord_util.load_imagenet_for_training(args)

    else:
        print("Loading synthetic data.")
        (labels, images) = ofrecord_util.load_synthetic(args)
    logits = model_dict[args.model](images,
                                    need_transpose=False if args.train_data_dir else True)
    if args.label_smoothing > 0:
        one_hot_labels = label_smoothing(labels, args.num_classes, args.label_smoothing, logits.dtype)
        loss = oneflow.nn.softmax_cross_entropy_with_logits(one_hot_labels, logits, name="softmax_loss")
    else:
        loss = oneflow.nn.sparse_softmax_cross_entropy_with_logits(labels, logits, name="softmax_loss")

    lr_scheduler = oneflow.optimizer.PiecewiseConstantScheduler([], [0.1])
    oneflow.optimizer.SGD(lr_scheduler, momentum=0.9).minimize(loss)
    # oneflow.losses.add_loss(loss)
    predictions = oneflow.nn.softmax(logits)
    outputs = {"loss": loss, "predictions": predictions, "labels": labels}
    return outputs

@oneflow.global_function("predict", get_val_config(args))
def InferenceNet():
    if args.val_data_dir:
        assert os.path.exists(args.val_data_dir)
        print("Loading data from {}".format(args.val_data_dir))
        (labels, images) = ofrecord_util.load_imagenet_for_validation(args)

    else:
        print("Loading synthetic data.")
        (labels, images) = ofrecord_util.load_synthetic(args)

    logits = model_dict[args.model](
        images, need_transpose=False if args.val_data_dir else True)
    predictions = oneflow.nn.softmax(logits)
    outputs = {"predictions": predictions, "labels": labels}
    return outputs

def main():
    InitNodes(args)
    oneflow.env.grpc_use_no_signal()
    oneflow.env.log_dir(args.log_dir)
    summary = Summary(args.log_dir, args)
    snapshot = Snapshot(args.model_save_dir, args.model_load_dir)

    for epoch in range(args.num_epochs):
        metric = Metric(
            desc='train', calculate_batches=args.loss_print_every_n_iter,
            summary=summary, save_summary_steps=epoch_size,
            batch_size=train_batch_size, loss_key='loss'
        )
        for i in range(epoch_size):
            TrainNet().async_get(metric.metric_cb(epoch, i))

        if args.val_data_dir:
            metric = Metric(desc='validation', calculate_batches=num_val_steps, summary=summary,
                            save_summary_steps=num_val_steps, batch_size=val_batch_size)
            for i in range(num_val_steps):
                InferenceNet().async_get(metric.metric_cb(epoch, i))

        snapshot.save('epoch_{}'.format(epoch))
if __name__ == "__main__":
    main()