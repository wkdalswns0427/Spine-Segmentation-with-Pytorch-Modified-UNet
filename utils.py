import torch
import torch.nn as nn
import torchvision
import numpy as np
from dataset import SpineDataset
from torch.utils.data import DataLoader
import gc


def save_checkpoint(state, filename="trained_models/final.pth.tar"):
    print("=> Saving checkpoint")
    torch.save(state, filename)


def load_checkpoint(checkpoint, model):
    print("=> Loading checkpoint")
    model.load_state_dict(checkpoint["state_dict"])


def get_loaders(
    train_dir,
    train_maskdir,
    val_dir,
    val_maskdir,
    batch_size,
    train_transform,
    val_transform,
    num_workers=4,
    pin_memory=True,
):
    train_ds = SpineDataset(
        image_dir=train_dir,
        mask_dir=train_maskdir,
        transform=train_transform,
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=pin_memory,
        shuffle=True,
    )

    val_ds = SpineDataset(
        image_dir=val_dir,
        mask_dir=val_maskdir,
        transform=val_transform,
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=pin_memory,
        shuffle=False,
    )

    return train_loader, val_loader

def get_test_loader(
    test_dir,
    batch_size,
    train_transform,
    num_workers=4,
    pin_memory=True,
):
    test_ds = SpineDataset(
        image_dir=test_dir,
        transform=train_transform,
    )

    test_loader = DataLoader(
        test_ds,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=pin_memory,
        shuffle=True,
    )
    return test_loader


def check_accuracy(loader, model, device="cuda"):
    num_correct = 0
    num_pixels = 0
    dice_score = 0
    model.eval()

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device).unsqueeze(1)
            preds = torch.sigmoid(model(x))
            preds = (preds > 0.5).float()
            num_correct += (preds == y).sum()
            num_pixels += torch.numel(preds)
            dice_score += (2 * (preds * y).sum()) / (
                (preds + y).sum() + 1e-8
            )
            #multiclass dice needs modification?

    print(
        f"Got {num_correct}/{num_pixels} with acc {num_correct/num_pixels*100:.2f}"
    )
    print(f"Dice score: {dice_score/len(loader)}")
    model.train()


def save_predictions_as_imgs(
    loader, model, folder="saved_images/", device="cuda"
):
    model.eval()
    for idx, (x, y) in enumerate(loader.dataset):
        if x.ndim == 3:
            x = x.unsqueeze(0)
        x = x.to(device=device)
        with torch.no_grad():
            preds = torch.round(torch.sigmoid(model(x))).cpu()
            preds = preds.squeeze(0).permute(1, 2, 0).numpy()
        np.save(
            f"{folder}/pred_{idx}.npy", preds
        )  # probability
        # torchvision.utils.save_image(y.unsqueeze(1), f"{folder}{idx}.png")

    model.train()

def save_result_as_numpy(
    loader, model, folder="numpy_results/", device="cuda"
):
    model.eval()
    for idx, (x) in enumerate(loader.dataset):
        gc.collect()
        torch.cuda.empty_cache()
        if idx<30:
            idx+=121
        elif 29<idx<50 :
            idx+=131
        else:
            idx+=141
        if x.ndim == 3:
            x = x.unsqueeze(0)
        x = x.to(device=device)
        print(x.shape)
        with torch.no_grad():
            preds = model(x).cpu()
            preds = torch.round(preds.sigmoid())
            preds = preds.squeeze(0).permute(1, 2, 0).numpy()
            preds = preds.astype(np.uint8)
            print(preds.dtype)
        np.save(
            f"{folder}/{idx}.npy", preds
        )
    model.train()