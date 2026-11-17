"""Optional gradient saliency stability; never silently substitute explanations."""
import numpy as np

def cosine_stability(a,b):
    a=np.asarray(a,dtype=float).ravel();b=np.asarray(b,dtype=float).ravel()
    if a.shape!=b.shape:raise ValueError('attribution shapes mismatch')
    den=np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.dot(a,b)/den) if den>1e-12 else None

def gradient_saliency(model,tensor,target=None):
    """Single-image torch tensor BCHW, B=1; returns abs gradient aggregated channels."""
    import torch
    if tensor.ndim!=4 or tensor.shape[0]!=1:raise ValueError('batch size must be 1')
    x=tensor.detach().clone().requires_grad_(True)
    model.eval();model.zero_grad(set_to_none=True)
    logits=model(x);logits=logits.logits if hasattr(logits,'logits') else logits
    if isinstance(logits,(tuple,list)):logits=logits[0]
    cls=int(logits.argmax(1).item()) if target is None else int(target)
    logits[0,cls].backward()
    return x.grad.detach().abs().mean(dim=1)[0].cpu().numpy()

def captum_attributions(model,tensor,target,method='integrated_gradients',steps=16):
    """Optional Captum; small default steps to limit GPU memory."""
    from captum.attr import IntegratedGradients,Saliency,InputXGradient,GradientShap
    import torch
    choices={'integrated_gradients':IntegratedGradients,'saliency':Saliency,'input_x_gradient':InputXGradient,'gradient_shap':GradientShap}
    if method not in choices:raise ValueError('unsupported Captum method')
    x=tensor.detach().clone().requires_grad_(True);model.eval()
    obj=choices[method](model)
    if method=='integrated_gradients':a=obj.attribute(x,baselines=torch.zeros_like(x),target=target,n_steps=steps,internal_batch_size=1)
    elif method=='gradient_shap':a=obj.attribute(x,baselines=torch.cat([torch.zeros_like(x),x*.5],dim=0),target=target,n_samples=steps,stdevs=0.0)
    else:a=obj.attribute(x,target=target)
    return a.detach().abs().mean(dim=1)[0].cpu().numpy()
