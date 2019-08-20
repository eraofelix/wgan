## Wasserstein GAN

Tensorflow implementation of Wasserstein GAN.

https://zhuanlan.zhihu.com/p/25071913

Two versions:
- wgan.py: the original clipping method.
- wgan_v2.py: the gradient penalty method. (Improved Training of Wasserstein GANs).

How to run (an example):

```
python wgan_v2.py --data mnist --model mlp --gpus 0
```
