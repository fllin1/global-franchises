
import { FranchiseMatch } from '@/types';

export async function searchFranchises(query: string): Promise<FranchiseMatch[]> {
    try {
        const url = query 
            ? `http://127.0.0.1:8000/api/franchises/search?q=${encodeURIComponent(query)}`
            : `http://127.0.0.1:8000/api/franchises/search`;

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
        const response = await fetch(`http://127.0.0.1:8000/api/franchises/${id}/territories`, {
            cache: 'no-store'
        });
        if (!response.ok) throw new Error('Failed to fetch territories');
        return await response.json();
    } catch (error) {
        console.error(`Error fetching territories for ${id}:`, error);
        throw error;
    }
}
