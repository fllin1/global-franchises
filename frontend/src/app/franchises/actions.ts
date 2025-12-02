
import { FranchiseMatch, FamilyBrand, FamilyBrandDetail } from '@/types';
import { getApiUrl } from '@/lib/api';

export async function searchFranchises(query: string): Promise<FranchiseMatch[]> {
    try {
        const url = query 
            ? getApiUrl(`/api/franchises/search?q=${encodeURIComponent(query)}`)
            : getApiUrl('/api/franchises/search');

        const response = await fetch(url, {
            cache: 'no-store'
        });
        if (!response.ok) throw new Error('Failed to search franchises');
        
        const data = await response.json();
        return data.map((item: any) => ({
            id: String(item.id),
            name: item.franchise_name,
            description: item.description_text || '',
            investment_min: item.total_investment_min_usd || 0,
            match_score: 0, // Not relevant for direct search
            why_narrative: '',
            primary_category: item.primary_category
        }));
    } catch (error) {
        console.error('Error searching franchises:', error);
        return [];
    }
}

export async function getFranchiseTerritories(id: number): Promise<any> {
    try {
        const response = await fetch(getApiUrl(`/api/franchises/${id}/territories`), {
            cache: 'no-store'
        });
        if (!response.ok) throw new Error('Failed to fetch territories');
        return await response.json();
    } catch (error) {
        console.error(`Error fetching territories for ${id}:`, error);
        throw error;
    }
}

// --- Family Brands Actions ---

export async function getFamilyBrands(query?: string): Promise<FamilyBrand[]> {
    try {
        const url = query 
            ? getApiUrl(`/api/family-brands/?q=${encodeURIComponent(query)}`)
            : getApiUrl('/api/family-brands/');

        const response = await fetch(url, {
            cache: 'no-store'
        });
        if (!response.ok) throw new Error('Failed to fetch family brands');
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching family brands:', error);
        return [];
    }
}

export async function getFamilyBrandDetail(id: number): Promise<FamilyBrandDetail | null> {
    try {
        const response = await fetch(getApiUrl(`/api/family-brands/${id}`), {
            cache: 'no-store'
        });
        if (!response.ok) {
            if (response.status === 404) return null;
            throw new Error('Failed to fetch family brand');
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching family brand ${id}:`, error);
        return null;
    }
}
