import os
import time
import argparse
import importlib
import tensorflow as tf
import tensorflow.contrib as tc

from visualize import *


class WassersteinGAN(object):
    def __init__(self, g_net, d_net, x_sampler, z_sampler, data, model):
        self.model = model
        self.data = data
        self.g_net = g_net
        self.d_net = d_net
        self.x_sampler = x_sampler
        self.z_sampler = z_sampler
        self.x_dim = self.d_net.x_dim
        self.z_dim = self.g_net.z_dim
        self.x = tf.placeholder(tf.float32, [None, self.x_dim], name='x')
        self.z = tf.placeholder(tf.float32, [None, self.z_dim], name='z')

        self.x_ = self.g_net(self.z)

        self.d = self.d_net(self.x, reuse=False)
        self.d_ = self.d_net(self.x_)

        self.g_loss = tf.reduce_mean(self.d_)
        self.d_loss = tf.reduce_mean(self.d) - tf.reduce_mean(self.d_)

        self.reg = tc.layers.apply_regularization(
            tc.layers.l1_regularizer(2.5e-5),
            weights_list=[
                var for var in tf.global_variables() if 'weights' in var.name]
        )
        self.g_loss_reg = self.g_loss + self.reg
        self.d_loss_reg = self.d_loss + self.reg
        with tf.control_dependencies(tf.get_collection(tf.GraphKeys.UPDATE_OPS)):
            self.d_rmsprop = tf.train.RMSPropOptimizer(learning_rate=5e-5)\
                .minimize(self.d_loss_reg, var_list=self.d_net.vars)
            self.g_rmsprop = tf.train.RMSPropOptimizer(learning_rate=5e-5)\
                .minimize(self.g_loss_reg, var_list=self.g_net.vars)

        self.d_clip = [v.assign(tf.clip_by_value(v, -0.01, 0.01))
                       for v in self.d_net.vars]
        gpu_options = tf.GPUOptions(allow_growth=True)
        self.sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))

    def train(self, batch_size=64, num_batches=1000000):
        plt.ion()
        self.sess.run(tf.global_variables_initializer())
        start_time = time.time()
        for t in range(0, num_batches):
            d_iters = 5
            if t % 500 == 0 or t < 25:
                d_iters = 100

            for _ in range(0, d_iters):
                bx = self.x_sampler(batch_size)
                bz = self.z_sampler(batch_size, self.z_dim)
                self.sess.run(self.d_clip)
                self.sess.run(
                    self.d_rmsprop, feed_dict={
                        self.x: bx, self.z: bz})

            bz = self.z_sampler(batch_size, self.z_dim)
            self.sess.run(self.g_rmsprop, feed_dict={self.z: bz, self.x: bx})

            # validation
            T = 100
            if t % T == 0:
                bx = self.x_sampler(batch_size)
                bz = self.z_sampler(batch_size, self.z_dim)

                d_loss = self.sess.run(
                    self.d_loss, feed_dict={self.x: bx, self.z: bz}
                )
                g_loss = self.sess.run(
                    self.g_loss, feed_dict={self.z: bz, self.x: bx}
                )
                print('Iter [%8d] Time [%5.4f] d_loss [%.4f] g_loss [%.4f]' %
                      (t, time.time() - start_time, d_loss - g_loss, g_loss))

            if t % T == 0:
                bz = self.z_sampler(batch_size, self.z_dim)
                bx = self.sess.run(self.x_, feed_dict={self.z: bz})
                bx = xs.data2img(bx)
                fig = plt.figure(self.data + '.' + self.model)
                grid_show(fig, bx, xs.shape)
                fig.savefig('logs/{}_{}.pdf'.format(self.data, t / 100))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('')
    parser.add_argument('--data', type=str, default='mnist')
    parser.add_argument('--model', type=str, default='dcgan')
    parser.add_argument('--gpus', type=str, default='0')
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = args.gpus
    data = importlib.import_module(args.data)
    model = importlib.import_module(args.data + '.' + args.model)
    xs = data.DataSampler()
    zs = data.NoiseSampler()
    d_net = model.Discriminator()
    g_net = model.Generator()
    wgan = WassersteinGAN(g_net, d_net, xs, zs, args.data, args.model)
    wgan.train()
